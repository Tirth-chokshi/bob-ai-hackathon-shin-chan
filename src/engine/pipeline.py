import gc
import json
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Callable
from config import RUNS, TIME_WINDOW, MIN_EDGE_WEIGHT
from engine.schema import Post
from engine.coordination import build_graph, NETWORK_STAGES
from engine.campaigns import find_campaigns

log = logging.getLogger(__name__)

# Stages reported to the UI while a dataset is analysed (in order)
STAGES = [
    "Reading posts",
    "Saving posts",
    "Preparing coordination database",
    *NETWORK_STAGES.values(),
    "Finding, scoring and profiling campaigns",
    "Writing graph and timeline",
]
TIMELINE_BUCKETS = [60, 300, 900, 3600, 6 * 3600, 86400, 7 * 86400]
MAX_TIMELINE_POINTS = 3000
SAMPLE_POSTS = 20  # per campaign: shown in the UI, sent to Bob, used as brief evidence


def spread_sample(posts: list[Post], n: int = SAMPLE_POSTS) -> list[Post]:
    """The first posts plus evenly spaced ones up to the last, oldest first, so a call to gather made
    hours after the rumour started is still in what the analyst and Bob see."""
    posts = sorted(posts, key=lambda p: (p.created_at, p.post_id))
    if len(posts) <= n:
        return posts
    head, rest = posts[:3], posts[3:]
    step = (len(rest) - 1) / (n - 4)
    return head + [rest[round(i * step)] for i in range(n - 3)]


def analyze(
    dataset_id: str,
    posts: list[Post],
    output_dir: Path | None = None,
    window: int = TIME_WINDOW,
    min_weight: int = MIN_EDGE_WEIGHT,
    progress: Callable[[str], None] = lambda stage: None,
    zone: str = "UTC",
) -> dict:
    """
    Executes the end-to-end CIB analysis pipeline for a dataset and writes to <output_dir>/<dataset_id>/:
    posts.json, campaigns.json, samples.json (first posts per campaign), graph.json (Cytoscape), timeline.json.
    """
    start_time = time.perf_counter()

    base_dir = output_dir if output_dir is not None else RUNS
    run_dir = base_dir / dataset_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save normalized posts.json (no indent: uploads can be 100k+ posts)
    progress("Saving posts")
    (run_dir / "posts.json").write_text(json.dumps([p.model_dump() for p in posts]), encoding="utf-8")

    # 2. Build multi-signal coordination graph
    G = build_graph(posts, db_path=run_dir / "toolkit.db", window=window, min_weight=min_weight, progress=progress)
    # The toolkit database is scratch space; close its lingering connections and remove it (can be 100s of MB)
    gc.collect()
    try:
        (run_dir / "toolkit.db").unlink(missing_ok=True)
    except OSError:
        log.warning("Could not remove %s; it is still in use", run_dir / "toolkit.db")

    # 3. Detect campaigns & score them
    progress("Finding, scoring and profiling campaigns")
    campaigns = find_campaigns(G, posts, min_size=5, window=window)

    # 4. Save campaigns.json. Campaign IDs are ranks, so if a campaign now has different accounts or posts
    # the cached Bob verdicts and summary may describe a different campaign: drop them.
    campaigns_path = run_dir / "campaigns.json"
    new_campaigns = [c.model_dump() for c in campaigns]
    old_campaigns = json.loads(campaigns_path.read_text(encoding="utf-8")) if campaigns_path.exists() else []
    identity = lambda cs: [(c["id"], sorted(c["accounts"]), sorted(c["post_ids"]), c["score"]) for c in cs]
    if identity(old_campaigns) != identity(new_campaigns):
        shutil.rmtree(run_dir / "bob", ignore_errors=True)
    campaigns_path.write_text(json.dumps(new_campaigns, indent=2), encoding="utf-8")

    # 5. First posts of each campaign, so nothing downstream has to reload posts.json
    progress("Writing graph and timeline")
    posts_by_id = {p.post_id: p for p in posts}
    samples = {c.id: [p.model_dump() for p in spread_sample([posts_by_id[pid] for pid in c.post_ids])] for c in campaigns}
    (run_dir / "samples.json").write_text(json.dumps(samples, indent=2), encoding="utf-8")

    # 6. Cytoscape graph.json (nodes & edges)
    acc_to_camp = {acc: c.id for c in campaigns for acc in c.accounts}
    user_map = {p.account_id: p.username for p in posts}
    first_seen = {}
    for p in posts:
        first_seen[p.account_id] = min(first_seen.get(p.account_id, p.created_at), p.created_at)
    roles = {a["account_id"]: "amplifier" for c in campaigns for a in c.amplifiers}
    roles.update({s["account_id"]: "seed" for c in campaigns for s in c.seeds})
    nodes = []
    for node in G.nodes():
        raw_label = G.nodes[node].get("username") or user_map.get(node, str(node))
        nodes.append({"data": {
            "id": str(node),
            "label": raw_label if raw_label.startswith("@") else f"@{raw_label}",
            "campaign": acc_to_camp.get(node),
            "degree": G.degree(node),
            "role": roles.get(node, "member") if node in acc_to_camp else None,
            "first_seen": first_seen.get(node),
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
    # buckets start on the dataset's local hour/day (IST is UTC+5:30, so UTC-aligned hours would read 10:30, 11:30…)
    offset = int(ZoneInfo(zone).utcoffset(datetime.fromtimestamp(first)).total_seconds())
    start = (first + offset) // bucket * bucket - offset
    points = [{"t": start + i * bucket, "total": 0, **{cid: 0 for cid in camp_ids}}
              for i in range((last - start) // bucket + 1)]
    for p in posts:
        pt = points[(p.created_at - start) // bucket]
        pt["total"] += 1
        if (cid := acc_to_camp.get(p.account_id)):
            pt[cid] += 1
    (run_dir / "timeline.json").write_text(
        json.dumps({"bucket_seconds": bucket, "campaign_ids": camp_ids, "points": points}), encoding="utf-8")

    return {
        "dataset_id": dataset_id,
        "posts": len(posts),
        "accounts": len({p.account_id for p in posts}),
        "runtime_ms": int((time.perf_counter() - start_time) * 1000),
        "campaigns": new_campaigns,
    }
