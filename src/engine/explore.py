"""Reads a dataset's posts from its X database (x.db) for the Posts view (an X-style timeline and threads) and the
"at a glance" numbers.

Nothing is invented: counts are X's own public_metrics when the data has them, never fewer than the replies, reposts
and quotes found inside this dataset; without public_metrics they are the ones found in the dataset, and the response
says which.
"""
import json
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

from engine.xstore import open_db, read_posts

FACETS = ("platform", "language", "city")
KINDS = {  # the Posts view's "post type" filter
    "original": lambda p: not p.get("repost_of") and not p.get("reply_to"),
    "replies": lambda p: bool(p.get("reply_to")),
    "reposts": lambda p: bool(p.get("repost_of")),
    "quotes": lambda p: bool(p.get("quote_of")),
    "media": lambda p: bool(p.get("media")),
}


class Run:
    """All posts of a run, oldest first, with who replied to, reposted and quoted each one."""

    def __init__(self, posts: list[dict], campaigns: list[dict], context: list[dict] = ()):
        """posts: the dataset (X API `data`); context: referenced posts from includes.tweets, shown in repost and
        quote cards and threads but never listed or counted as part of the dataset."""
        campaign_of = {pid: c["id"] for c in campaigns for pid in c["post_ids"]}
        posts.sort(key=lambda p: p["created_at"])
        self.posts = posts
        self.by_id = {**{p["post_id"]: {**p, "campaign": None, "context": True} for p in context},
                      **{p["post_id"]: p for p in posts}}
        self.replies, self.reposts, self.quotes = defaultdict(list), defaultdict(list), defaultdict(list)
        for p in posts:
            p["campaign"] = campaign_of.get(p["post_id"])
            p["_search"] = f"{p['text']} {p['username']} {p['account_id']} {p.get('display_name') or ''}".lower()
            for target, index in ((p.get("reply_to"), self.replies), (p.get("repost_of"), self.reposts),
                                  (p.get("quote_of"), self.quotes)):
                if target:
                    index[target].append(p)

    def counts(self, p: dict) -> dict:
        """The platform's counts when the source has them, else what this dataset holds; "source" says which."""
        found = {"replies": len(self.replies[p["post_id"]]), "reposts": len(self.reposts[p["post_id"]]),
                 "quotes": len(self.quotes[p["post_id"]])}
        if p.get("metrics"):  # the platform's count, but never fewer than the dataset itself holds
            m = p["metrics"]
            return {**m, **{k: max(v, m.get(k, 0)) for k, v in found.items()}, "source": "platform"}
        return {**found, "source": "dataset"}

    def card(self, p: dict, depth: int = 1) -> dict:
        """A post as the timeline shows it: counts, who it replies to, and the reposted or quoted post if present."""
        c = {k: v for k, v in p.items() if k != "_search"}
        c["counts"] = self.counts(p)
        parent = self.by_id.get(p.get("reply_to"))
        c["replying_to"] = parent["username"] if parent else p.get("reply_to_user")
        if depth:
            for key, target in (("original", p.get("repost_of")), ("quoted", p.get("quote_of"))):
                if target in self.by_id:
                    c[key] = self.card(self.by_id[target], depth - 1)
        return c

    def score(self, p: dict) -> int:
        """For the "Top" tab: engagement the platform reported, else reposts, quotes and replies inside the dataset."""
        m = p.get("metrics") or {}
        if m:
            return m.get("likes", 0) + 2 * m.get("reposts", 0) + 2 * m.get("quotes", 0) + m.get("replies", 0)
        pid = p["post_id"]
        return 2 * len(self.reposts[pid]) + 2 * len(self.quotes[pid]) + len(self.replies[pid])


@lru_cache(maxsize=2)  # ponytail: the last two datasets stay in memory (a 250k-post run is a few hundred MB)
def _load(run_dir: str, db_mtime: float, campaigns_mtime: float) -> Run:
    db = open_db(Path(run_dir))  # the dataset's X database (engine/xstore.py)
    try:
        posts, context = read_posts(db), read_posts(db, source="includes")
    finally:
        db.close()
    campaigns_path = Path(run_dir) / "campaigns.json"
    campaigns = json.loads(campaigns_path.read_text(encoding="utf-8")) if campaigns_path.exists() else []
    return Run([p.model_dump() for p in posts], campaigns, [p.model_dump() for p in context])


def load_run(run_dir: Path) -> Run:
    db, campaigns = run_dir / "x.db", run_dir / "campaigns.json"
    if not db.exists():
        raise FileNotFoundError("This dataset has no X database. Upload it again as X API v2 JSON.")
    return _load(str(run_dir), db.stat().st_mtime, campaigns.stat().st_mtime if campaigns.exists() else 0)


def run_posts(run_dir: Path) -> list[dict]:
    return load_run(run_dir).posts


def dataset_stats(run_dir: Path) -> dict:
    """Counts for the Overview's "at a glance" line; saved next to the posts and redone when they change."""
    path, posts_path = run_dir / "stats.json", run_dir / "x.db"
    if path.exists() and path.stat().st_mtime >= posts_path.stat().st_mtime:
        return json.loads(path.read_text(encoding="utf-8"))
    posts = run_posts(run_dir)
    stats = {
        "posts": len(posts),
        "accounts": len({p["account_id"] for p in posts}),
        "first": posts[0]["created_at"] if posts else None,
        "last": posts[-1]["created_at"] if posts else None,
        **{f"{f}s": dict(Counter(p.get(f) for p in posts if p.get(f)).most_common(8)) for f in FACETS},
        "cities_total": len({p.get("city") for p in posts if p.get("city")}),
        "hashtags": dict(Counter(h for p in posts for h in p["hashtags"]).most_common(5)),
        "links": len({u for p in posts for u in p["urls"]}),
        "reposts": sum(bool(p.get("repost_of")) for p in posts),
        "replies": sum(bool(p.get("reply_to")) for p in posts),
    }
    path.write_text(json.dumps(stats, ensure_ascii=False), encoding="utf-8")
    return stats


def search_posts(run_dir: Path, q: str = "", offset: int = 0, limit: int = 50, sort: str = "latest", kind: str = "",
                 **filters) -> dict:
    """Posts matching every filter (campaign, account, hashtag, platform, language, city, reply_to, repost_of,
    quote_of, kind) and the search words, sorted latest, oldest or top. Facets are over the matches."""
    run = load_run(run_dir)
    words = q.lower().split()
    hashtag = (filters.pop("hashtag", None) or "").lower()
    account = filters.pop("account", None)
    wanted = {k: v for k, v in filters.items() if v}
    matches = [
        p for p in run.posts
        if all(w in p["_search"] for w in words)
        and (not account or p["account_id"] == account or p["username"].lower() == account.lower().lstrip("@"))
        and (not hashtag or hashtag in (h.lower() for h in p["hashtags"]))
        and all(str(p.get(k)) == v for k, v in wanted.items())
    ]
    kinds = {"all": len(matches), **{k: sum(map(f, matches)) for k, f in KINDS.items()}}  # counted before the post-type filter, as menus show
    if kind in KINDS:
        matches = [p for p in matches if KINDS[kind](p)]
    if sort == "top":
        matches = sorted(matches, key=run.score, reverse=True)
    elif sort != "oldest":
        matches = matches[::-1]
    accounts = Counter(p["account_id"] for p in matches)
    names = {p["account_id"]: (p["username"], p.get("display_name")) for p in matches}
    return {
        "total": len(matches),
        "posts": [run.card(p) for p in matches[offset:offset + limit]],
        "facets": {
            **{f: dict(Counter(p.get(f) for p in matches if p.get(f)).most_common(12)) for f in FACETS},
            "campaign": dict(Counter(p["campaign"] for p in matches if p["campaign"]).most_common()),
            "hashtag": dict(Counter(h for p in matches for h in p["hashtags"]).most_common(8)),
            "kind": kinds,
            "accounts": [{"account_id": a, "username": names[a][0], "display_name": names[a][1], "posts": n}
                         for a, n in accounts.most_common(5)],
        },
    }


def thread(run_dir: Path, post_id: str) -> dict:
    """One post as X shows it when opened: the posts it replies to above, its replies below, who reposted it and
    who quoted it. Only posts in this dataset can be shown; the counts say when the platform saw more."""
    run = load_run(run_dir)
    post = run.by_id.get(post_id)
    if not post:
        raise KeyError(post_id)
    ancestors, cursor = [], post
    while cursor.get("reply_to") in run.by_id and len(ancestors) < 25:
        cursor = run.by_id[cursor["reply_to"]]
        ancestors.insert(0, run.card(cursor))
    return {
        "ancestors": ancestors,
        "missing_parent": bool(cursor.get("reply_to")) and cursor.get("reply_to") not in run.by_id,
        "post": run.card(post),
        "replies": [run.card(r) for r in run.replies[post_id][:200]],
        "reposted_by": [{"account_id": r["account_id"], "username": r["username"], "display_name": r.get("display_name"),
                         "created_at": r["created_at"], "campaign": r["campaign"], "post_id": r["post_id"]}
                        for r in run.reposts[post_id][:500]],
        "quotes": [run.card(r) for r in run.quotes[post_id][:200]],
    }
