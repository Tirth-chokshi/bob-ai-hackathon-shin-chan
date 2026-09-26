import json
import time
from collections import defaultdict
from pathlib import Path
from config import RUNS, TIME_WINDOW, MIN_EDGE_WEIGHT
from engine.schema import Post, Campaign
from engine.coordination import build_graph
from engine.campaigns import find_campaigns


def analyze(
    dataset_id: str,
    posts: list[Post],
    output_dir: Path | None = None,
    window: int = TIME_WINDOW,
    min_weight: int = MIN_EDGE_WEIGHT
) -> dict:
    """
    Executes the end-to-end CIB analysis pipeline for a dataset:
    1. Ingests normalized posts
    2. Builds coordination network graph
    3. Finds coordinated campaigns via Louvain community detection
    4. Computes explainable CIB risk scores
    5. Generates Cytoscape graph.json and activity timeline.json
    6. Persists all run artifacts to data/runs/<dataset_id>/
    """
    start_time = time.perf_counter()

    base_dir = output_dir if output_dir is not None else RUNS
    run_dir = base_dir / dataset_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "bob").mkdir(parents=True, exist_ok=True)

    # 1. Save normalized posts.json
    posts_path = run_dir / "posts.json"
    with open(posts_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in posts], f, indent=2)

    # 2. Build multi-signal coordination graph
    db_path = run_dir / "toolkit.db"
    G = build_graph(posts, db_path=db_path, window=window, min_weight=min_weight)

    # 3. Detect campaigns & score them
    campaigns = find_campaigns(G, posts, min_size=5, window=window)

    # 4. Save campaigns.json
    campaigns_path = run_dir / "campaigns.json"
    with open(campaigns_path, "w", encoding="utf-8") as f:
        json.dump([c.model_dump() for c in campaigns], f, indent=2)

    # 5. Build Cytoscape graph.json (nodes & edges)
    acc_to_camp = {acc: c.id for c in campaigns for acc in c.accounts}
    user_map = {p.account_id: p.username for p in posts}

    nodes = []
    for node in G.nodes():
        degree = G.degree(node)
        raw_label = G.nodes[node].get("username") or user_map.get(node, str(node))
        label = raw_label if raw_label.startswith("@") else f"@{raw_label}"
        camp_id = acc_to_camp.get(node)
        nodes.append({
            "data": {
                "id": str(node),
                "label": label,
                "campaign": camp_id,
                "degree": degree
            }
        })

    edges = []
    for u, v, data in G.edges(data=True):
        edge_id = f"{u}__{v}"
        edges.append({
            "data": {
                "id": edge_id,
                "source": str(u),
                "target": str(v),
                "weight": data.get("weight", 1),
                "signals": data.get("signals", [])
            }
        })

    graph_path = run_dir / "graph.json"
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump({"nodes": nodes, "edges": edges}, f, indent=2)

    # 6. Build timeline.json (60s buckets)
    camp_ids = [c.id for c in campaigns]
    bucket_map = defaultdict(lambda: {"total": 0, **{cid: 0 for cid in camp_ids}})

    for p in posts:
        b_time = (p.created_at // 60) * 60
        bucket_map[b_time]["total"] += 1
        c_id = acc_to_camp.get(p.account_id)
        if c_id:
            bucket_map[b_time][c_id] += 1

    timeline_points = [
        {"t": t, **counts}
        for t, counts in sorted(bucket_map.items())
    ]

    timeline_path = run_dir / "timeline.json"
    with open(timeline_path, "w", encoding="utf-8") as f:
        json.dump({
            "bucket_seconds": 60,
            "campaign_ids": camp_ids,
            "points": timeline_points
        }, f, indent=2)

    runtime_ms = int((time.perf_counter() - start_time) * 1000)
    unique_accounts = {p.account_id for p in posts}

    return {
        "dataset_id": dataset_id,
        "posts": len(posts),
        "accounts": len(unique_accounts),
        "runtime_ms": runtime_ms,
        "campaigns": [c.model_dump() for c in campaigns]
    }
