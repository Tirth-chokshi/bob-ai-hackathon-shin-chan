"""How a campaign spread: who started it, who amplified it, where it went, how fast, and when we could flag it.

Everything here is plain calculation on the posts and the coordination graph (no AI).
"""
from collections import Counter, defaultdict
import networkx as nx
from coordination_network_toolkit.similarity import message_preprocessor
from engine.schema import Post

REPLY_WINDOW = 300  # replies in a pile-on arrive over minutes (same as the co_reply network)


def _path(posts: list[Post], field: str) -> list[dict]:
    """[{name, first_seen, posts}] for each platform/town, in the order the campaign reached it."""
    first, count = {}, Counter()
    for p in posts:
        name = getattr(p, field)
        if name:
            first.setdefault(name, p.created_at)
            count[name] += 1
    return [{"name": n, "first_seen": t, "posts": count[n]} for n, t in sorted(first.items(), key=lambda kv: kv[1])]


def detection_time(posts: list[Post], window: int, min_weight: int = 2, min_size: int = 5) -> int | None:
    """Earliest time at which min_size of these accounts were linked by min_weight co-actions
    (same text, link, reply target or repost target within the window).

    Mirrors the engine's rule (MIN_EDGE_WEIGHT, min campaign size) but ignores similar-text links,
    so it is an upper bound: the full engine could flag the campaign at this time or earlier.
    """
    actions = defaultdict(list)  # (kind, key) -> [(time, account)]
    for p in posts:
        if p.text and (text := message_preprocessor(p.text)):
            actions[("text", text)].append((p.created_at, p.account_id))
        for u in p.urls:
            actions[("link", u)].append((p.created_at, p.account_id))
        if p.reply_to:
            actions[("reply", p.reply_to)].append((p.created_at, p.account_id))
        if p.repost_of:
            actions[("repost", p.repost_of)].append((p.created_at, p.account_id))

    # Like the engine, each kind of co-action is its own network: a pair needs min_weight of the same kind
    pair_times = defaultdict(list)  # (kind, a, b) -> times the pair acted together
    for (kind, _), items in actions.items():
        w = REPLY_WINDOW if kind == "reply" else window
        items.sort()
        for i, (t1, a1) in enumerate(items):
            for t2, a2 in items[i + 1:]:
                if t2 - t1 > w:
                    break
                if a1 != a2:
                    pair_times[(kind, *sorted((a1, a2)))].append(t2)

    edge_time = {}
    for (kind, a, b), ts in pair_times.items():
        if len(ts) >= min_weight:
            t = sorted(ts)[min_weight - 1]
            edge_time[(a, b)] = min(t, edge_time.get((a, b), t))
    edges = sorted((t, a, b) for (a, b), t in edge_time.items())
    parent, size = {}, {}

    def root(x):
        parent.setdefault(x, x)
        size.setdefault(x, 1)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for t, a, b in edges:
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[rb] = ra
            size[ra] += size[rb]
            if size[ra] >= min_size:
                return t
    return None


def profile_campaign(accounts: list[str], posts: list[Post], G: nx.Graph, window: int) -> dict:
    """Spread profile for one campaign; `posts` are all posts by its accounts."""
    posts = sorted(posts, key=lambda p: (p.created_at, p.post_id))
    usernames = {p.account_id: p.username for p in posts}

    # Who started it: the first accounts to post
    seeds, seen = [], set()
    for p in posts:
        if p.account_id not in seen:
            seen.add(p.account_id)
            seeds.append({
                "account_id": p.account_id, "username": p.username, "platform": p.platform, "city": p.city,
                "first_seen": p.created_at, "post_id": p.post_id, "text": p.text[:160],
                "account_age_days": (p.created_at - p.account_created_at) // 86400 if p.account_created_at else None,
            })
            if len(seeds) == 3:
                break

    # Who amplified it: most connected accounts inside the campaign
    degree = G.subgraph(accounts).degree(weight="weight")
    posts_per_account = Counter(p.account_id for p in posts)
    amplifiers = [
        {"account_id": a, "username": usernames.get(a, a), "links": round(d), "posts": posts_per_account[a]}
        for a, d in sorted(degree, key=lambda x: (-x[1], x[0]))[:5]  # ties broken by ID, so re-runs match
    ]

    # How fast: minutes until 10 accounts, and 90% of accounts, had posted
    first_post = {}
    for p in posts:
        first_post.setdefault(p.account_id, p.created_at)
    joined = sorted(first_post.values())

    def minutes_until(n):
        return round((joined[n - 1] - joined[0]) / 60) if 0 < n <= len(joined) else None

    creation = {p.account_id: p.account_created_at for p in posts if p.account_created_at}
    fresh = [a for a, c in creation.items() if first_post[a] - c < 30 * 86400]

    return {
        "seeds": seeds,
        "amplifiers": amplifiers,
        "platform_path": _path(posts, "platform"),
        "town_path": _path(posts, "city"),
        "languages": dict(Counter(p.language for p in posts if p.language).most_common()),
        "new_account_share": round(len(fresh) / len(creation), 2) if creation else None,
        "reach": {"to_10_accounts_min": minutes_until(10), "to_90pct_min": minutes_until(max(1, round(len(joined) * 0.9)))},
        "detected_at": detection_time(posts, window),
    }
