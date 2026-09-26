import logging
import os
from pathlib import Path
from typing import Callable
import networkx as nx
from coordination_network_toolkit import preprocess, graph, compute_networks as cn
from coordination_network_toolkit.similarity import MinDocSizeSimilarity
from engine.schema import Post

log = logging.getLogger(__name__)

NETWORKS = {
    "co_tweet": cn.compute_co_tweet_network,
    "co_similar_tweet": cn.compute_co_similar_tweet,
    "co_link": cn.compute_co_link_network,
    "co_reply": cn.compute_co_reply_network,
    "co_retweet": cn.compute_co_retweet_parallel,
}
# progress labels shown in the UI, one per network
NETWORK_STAGES = {
    "co_tweet": "Network 1/5: same text",
    "co_similar_tweet": "Network 2/5: similar text",
    "co_link": "Network 3/5: same link",
    "co_reply": "Network 4/5: replies to the same post",
    "co_retweet": "Network 5/5: same retweet",
}


def build_graph(
    posts: list[Post],
    db_path: Path | str,
    window: int = 60,
    min_weight: int = 2,
    progress: Callable[[str], None] = lambda stage: None,
) -> nx.Graph:
    """Builds a multi-signal coordination network graph from posts."""
    db_path = str(db_path)
    if os.path.exists(db_path):
        os.remove(db_path)

    # 1. Format rows for coordination toolkit
    # (post_id, account_id, username, repost_of or "", reply_to or "", text, created_at, urls)
    rows = [
        (
            p.post_id,
            p.account_id,
            p.username,
            p.repost_of or "",
            p.reply_to or "",
            p.text,
            p.created_at,
            p.urls
        )
        for p in posts
    ]

    progress("Preparing coordination database")
    preprocess.preprocess_data(db_path, rows)

    # 2. Compute individual networks
    for net_name, compute in NETWORKS.items():
        progress(NETWORK_STAGES[net_name])
        # replies in a pile-on arrive over minutes, so co_reply gets a 300s window at least
        net_window = max(window, 300) if net_name == "co_reply" else window
        # MinDocSizeSimilarity skips posts under 5 words; the default similarity divides by zero on empty posts
        extra = ({"similarity_threshold": 0.8, "similarity_function": MinDocSizeSimilarity(5)}
                 if net_name == "co_similar_tweet" else {})
        try:
            compute(db_path, time_window=net_window, min_edge_weight=min_weight, n_threads=1, **extra)
        except Exception:
            log.exception("%s network failed; continuing without it", net_name)

    # 3. Merge into unified undirected graph
    G = nx.Graph()

    # Track username map from posts
    user_map = {p.account_id: p.username for p in posts}

    for net_name in NETWORKS.keys():
        try:
            sub_g = graph.load_networkx_graph(db_path, net_name)
        except Exception:
            log.exception("could not load %s network", net_name)
            continue

        for u, v, data in sub_g.edges(data=True):
            w = data.get("weight", 1)
            if G.has_edge(u, v):
                G[u][v]["weight"] += w
                G[u][v]["signals"].add(net_name)
            else:
                G.add_edge(u, v, weight=w, signals={net_name})

            # Ensure nodes have usernames
            for node_id in (u, v):
                if "username" not in G.nodes[node_id]:
                    G.nodes[node_id]["username"] = (
                        sub_g.nodes.get(node_id, {}).get("username")
                        or user_map.get(node_id, str(node_id))
                    )

    # Convert signals sets to sorted lists for JSON serialization
    for _, _, data in G.edges(data=True):
        if isinstance(data.get("signals"), set):
            data["signals"] = sorted(list(data["signals"]))

    return G
