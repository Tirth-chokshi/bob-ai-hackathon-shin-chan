import json
import hashlib
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from config import RUNS, TIME_WINDOW, MIN_EDGE_WEIGHT
from engine.schema import Post
from engine.coordination import build_graph, NETWORK_STAGES
from engine.campaigns import find_campaigns

# Stages reported to the UI while a dataset is analysed (in order)
STAGES = [
    "Reading posts",
    "Saving posts",
    "Preparing coordination database",
    *NETWORK_STAGES.values(),
    "Finding and scoring campaigns",
    "Writing graph and timeline",
]
TIMELINE_BUCKETS = [60, 300, 900, 3600, 6 * 3600, 86400, 7 * 86400]
MAX_TIMELINE_POINTS = 3000
SAMPLE_POSTS = 20  # per campaign, oldest first: shown in the UI, sent to Bob, used as brief evidence


def analyze(
    dataset_id: str,
    posts: list[Post],
    output_dir: Path | None = None,
    window: int = TIME_WINDOW,
    min_weight: int = MIN_EDGE_WEIGHT,
    progress: Callable[[str], None] = lambda stage: None,
    input_sha256: str | None = None,
) -> dict:
    """
    Executes the end-to-end CIB analysis pipeline for a dataset and writes to <output_dir>/<dataset_id>/:
    posts.json, campaigns.json, samples.json (first posts per campaign), graph.json (Cytoscape), timeline.json.
    """
    start_time = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()

    base_dir = output_dir if output_dir is not None else RUNS
    run_dir = base_dir / dataset_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save normalized posts.json (no indent: uploads can be 100k+ posts)
    progress("Saving posts")
    (run_dir / "posts.json").write_text(json.dumps([p.model_dump() for p in posts]), encoding="utf-8")
    normalized_sha256 = hashlib.sha256((run_dir / "posts.json").read_bytes()).hexdigest()

    # 2. Build multi-signal coordination graph
    G = build_graph(posts, db_path=run_dir / "toolkit.db", window=window, min_weight=min_weight, progress=progress)

    # 3. Detect campaigns & score them
    progress("Finding and scoring campaigns")
    campaigns = find_campaigns(G, posts, min_size=5, window=window)

    # 4. Save campaigns.json. Campaign IDs are ranks, so if the campaigns changed
    # the cached Bob verdicts and summary may describe different campaigns: drop them.
    campaigns_path = run_dir / "campaigns.json"
    new_campaigns = [c.model_dump() for c in campaigns]
    old_campaigns = json.loads(campaigns_path.read_text(encoding="utf-8")) if campaigns_path.exists() else None
    if old_campaigns != new_campaigns:
        shutil.rmtree(run_dir / "bob", ignore_errors=True)
    campaigns_path.write_text(json.dumps(new_campaigns, indent=2), encoding="utf-8")

    # 5. First posts of each campaign, so nothing downstream has to reload posts.json
    progress("Writing graph and timeline")
    posts_by_id = {p.post_id: p for p in posts}
    samples = {
        c.id: [p.model_dump() for p in sorted((posts_by_id[pid] for pid in c.post_ids),
                                              key=lambda p: (p.created_at, p.post_id))[:SAMPLE_POSTS]]
        for c in campaigns
    }
    (run_dir / "samples.json").write_text(json.dumps(samples, indent=2), encoding="utf-8")

    # 6. Cytoscape graph.json (nodes & edges)
    acc_to_camp = {acc: c.id for c in campaigns for acc in c.accounts}
    user_map = {p.account_id: p.username for p in posts}
    nodes = []
    for node in G.nodes():
        raw_label = G.nodes[node].get("username") or user_map.get(node, str(node))
        nodes.append({"data": {
            "id": str(node),
            "label": raw_label if raw_label.startswith("@") else f"@{raw_label}",
            "campaign": acc_to_camp.get(node),
            "degree": G.degree(node),
        }})
    edges = [
        {"data": {"id": f"{u}__{v}", "source": str(u), "target": str(v),
                  "weight": data.get("weight", 1), "signals": data.get("signals", [])}}
        for u, v, data in G.edges(data=True)
    ]
    (run_dir / "graph.json").write_text(json.dumps({"nodes": nodes, "edges": edges}), encoding="utf-8")

    # 7. timeline.json: posts per bucket, bucket size grows with the time span (demo: 1 min, years of data: 1 day)
    camp_ids = [c.id for c in campaigns]
    first = min(p.created_at for p in posts) if posts else 0
    last = max(p.created_at for p in posts) if posts else 0
    bucket = next((b for b in TIMELINE_BUCKETS if (last - first) / b <= MAX_TIMELINE_POINTS), TIMELINE_BUCKETS[-1])
    start = first // bucket * bucket
    points = [{"t": start + i * bucket, "total": 0, **{cid: 0 for cid in camp_ids}}
              for i in range((last - start) // bucket + 1)]
    for p in posts:
        pt = points[(p.created_at - start) // bucket]
        pt["total"] += 1
        if (cid := acc_to_camp.get(p.account_id)):
            pt[cid] += 1
    (run_dir / "timeline.json").write_text(
        json.dumps({"bucket_seconds": bucket, "campaign_ids": camp_ids, "points": points}), encoding="utf-8")

    result = {
        "dataset_id": dataset_id,
        "posts": len(posts),
        "accounts": len({p.account_id for p in posts}),
        "runtime_ms": int((time.perf_counter() - start_time) * 1000),
        "campaigns": new_campaigns,
    }
    manifest = {
        "manifest_version": 1,
        "dataset_id": dataset_id,
        "schema_version": 1,
        "software_version": "0.3.0",
        "input_sha256": input_sha256,
        "normalized_posts_sha256": normalized_sha256,
        "configuration": {"window_seconds": window, "minimum_edge_weight": min_weight},
        "post_count": len(posts),
        "analysis_started_at": started_at,
        "analysis_completed_at": datetime.now(timezone.utc).isoformat(),
        "runtime_ms": result["runtime_ms"],
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return result
