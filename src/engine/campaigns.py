from collections import Counter
import networkx as nx
from engine.schema import Campaign, Post
from engine.scoring import score_campaign


def find_campaigns(
    G: nx.Graph,
    posts: list[Post],
    min_size: int = 5,
    window: int = 60
) -> list[Campaign]:
    """
    Detects coordinated communities via Louvain modularity optimization on G,
    extracts campaign metadata, computes explainable CIB scores, and orders
    campaigns by risk (c1, c2, ...).
    """
    if G.number_of_nodes() == 0:
        return []

    # Map posts by account
    posts_by_account: dict[str, list[Post]] = {}
    for p in posts:
        if p.account_id not in posts_by_account:
            posts_by_account[p.account_id] = []
        posts_by_account[p.account_id].append(p)

    # 1. Louvain community detection with fixed seed for determinism
    communities = nx.community.louvain_communities(G, weight="weight", seed=42)

    raw_campaigns = []
    for comm in communities:
        if len(comm) < min_size:
            continue

        accounts = sorted(list(comm))
        comm_posts = [p for acc in accounts for p in posts_by_account.get(acc, [])]
        if not comm_posts:
            continue

        post_ids = [p.post_id for p in comm_posts]
        size = len(accounts)
        first_seen = min(p.created_at for p in comm_posts)
        last_seen = max(p.created_at for p in comm_posts)

        # Top hashtag
        hashtag_counts = Counter(h for p in comm_posts for h in p.hashtags)
        top_hashtag = hashtag_counts.most_common(1)[0][0] if hashtag_counts else None

        # Internal signals
        signals_set = set()
        sub = G.subgraph(accounts)
        for _, _, data in sub.edges(data=True):
            sigs = data.get("signals", [])
            for s in sigs:
                signals_set.add(s)
        signals = sorted(list(signals_set))

        # Median account age in days (at campaign first_seen)
        age_days_list = []
        for acc in accounts:
            acc_posts = posts_by_account.get(acc, [])
            if acc_posts and acc_posts[0].account_created_at:
                age = max(0, (first_seen - acc_posts[0].account_created_at) // 86400)
                age_days_list.append(age)
        
        median_age = (
            sorted(age_days_list)[len(age_days_list) // 2]
            if age_days_list else None
        )

        # CIB Score & Feature breakdown
        score, features = score_campaign(
            campaign_posts=comm_posts,
            all_dataset_posts=posts,
            signals=signals,
            window=window
        )

        raw_campaigns.append({
            "accounts": accounts,
            "post_ids": post_ids,
            "size": size,
            "top_hashtag": top_hashtag,
            "score": score,
            "features": features,
            "signals": signals,
            "first_seen": first_seen,
            "last_seen": last_seen,
            "median_account_age_days": median_age,
        })

    # Sort descending by score, tie-break by size
    raw_campaigns.sort(key=lambda c: (c["score"], c["size"]), reverse=True)

    # Assign sequential IDs: c1, c2, ...
    campaigns: list[Campaign] = []
    for idx, c_data in enumerate(raw_campaigns, 1):
        campaigns.append(Campaign(
            id=f"c{idx}",
            accounts=c_data["accounts"],
            post_ids=c_data["post_ids"],
            size=c_data["size"],
            top_hashtag=c_data["top_hashtag"],
            score=c_data["score"],
            features=c_data["features"],
            signals=c_data["signals"],
            first_seen=c_data["first_seen"],
            last_seen=c_data["last_seen"],
            median_account_age_days=c_data["median_account_age_days"]
        ))

    return campaigns
