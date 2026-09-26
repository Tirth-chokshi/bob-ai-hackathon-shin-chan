import os
from pathlib import Path
import networkx as nx
from coordination_network_toolkit import preprocess, graph, compute_networks as cn
from engine.schema import Post

NETWORKS = {
    "co_tweet": cn.compute_co_tweet_network,
    "co_similar_tweet": cn.compute_co_similar_tweet,
    "co_link": cn.compute_co_link_network,
    "co_reply": cn.compute_co_reply_network,
    "co_retweet": cn.compute_co_retweet_parallel,
}


def build_graph(
    posts: list[Post],
    db_path: Path | str,
    window: int = 60,
    min_weight: int = 2
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

    preprocess.preprocess_data(db_path, rows)

    # 2. Compute individual networks
    # co_tweet
    try:
        cn.compute_co_tweet_network(db_path, time_window=window, min_edge_weight=min_weight, n_threads=1)
    except Exception:
        pass

    # co_similar_tweet with similarity_threshold=0.8
    try:
        cn.compute_co_similar_tweet(
            db_path,
            time_window=window,
            similarity_threshold=0.8,
            min_edge_weight=min_weight,
            n_threads=1
        )
    except Exception:
        pass

    # co_link
    try:
        cn.compute_co_link_network(db_path, time_window=window, min_edge_weight=min_weight, n_threads=1)
    except Exception:
        pass

    # co_reply (replies often take slightly longer in campaigns, up to 300s window)
    try:
        reply_window = max(window, 300)
        cn.compute_co_reply_network(db_path, time_window=reply_window, min_edge_weight=min_weight, n_threads=1)
    except Exception:
        pass

    # co_retweet
    try:
        cn.compute_co_retweet_parallel(db_path, time_window=window, min_edge_weight=min_weight, n_threads=1)
    except Exception:
        pass

    # 3. Merge into unified undirected graph
    G = nx.Graph()

    # Track username map from posts
    user_map = {p.account_id: p.username for p in posts}

    for net_name in NETWORKS.keys():
        try:
            sub_g = graph.load_networkx_graph(db_path, net_name)
        except Exception:
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
