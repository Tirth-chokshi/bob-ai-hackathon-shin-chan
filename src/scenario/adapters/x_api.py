"""X (Twitter) API data as Posts, without any conversion by the user.

Reads, in a .json or .jsonl file or as parsed objects:
- API v2 responses: {"data": [...], "includes": {"users", "tweets", "places", "media"}, "meta"} (recent/full-archive
  search, timelines, likes, quote and retweet lookups), one per file, a list of them, or one per line (twarc2 output)
- API v2 filtered-stream lines: {"data": {...}, "includes": ..., "matching_rules": [...]}
- v2 posts with the author embedded ("author": {...}, as twarc2's flatten writes them)
- v1.1 tweets: {"id_str", "user": {...}, "retweeted_status", "quoted_status", ...} (older archives and exports)

Everything the platform showed is kept: author name and handle, verified, followers, the counts (likes, reposts,
replies, quotes, views), quotes, the thread (conversation_id), who was replied to, media types, and the full text of
a reposted post (X's own text for a repost is cut short: "RT @user: …").

Field guide: https://docs.x.com/x-api/fundamentals/data-dictionary
"""
from engine.schema import Post

X_NO_LANGUAGE = {"und", "qme", "zxx", "qht", "qam", "qct", "qst"}
# public_metrics (v2) and the v1.1 count fields -> our metric names
V2_METRICS = {"like_count": "likes", "retweet_count": "reposts", "reply_count": "replies", "quote_count": "quotes",
              "impression_count": "views"}
V1_METRICS = {"favorite_count": "likes", "retweet_count": "reposts", "reply_count": "replies", "quote_count": "quotes"}


def _is_v2_page(o) -> bool:
    return isinstance(o, dict) and "data" in o and (isinstance(o["data"], dict) or isinstance(o["data"], list))


def _is_v2_post(o) -> bool:
    return isinstance(o, dict) and "id" in o and "text" in o and ("author_id" in o or "author" in o)


def _is_v1_tweet(o) -> bool:
    return isinstance(o, dict) and "id_str" in o and isinstance(o.get("user"), dict)


def is_x_data(obj) -> bool:
    """True for anything this adapter reads: a page, a stream line, a post, a v1.1 tweet, or a list of them."""
    first = obj[0] if isinstance(obj, list) and obj else obj
    return _is_v2_page(first) or _is_v2_post(first) or _is_v1_tweet(first)


def x_posts(obj) -> list[Post]:
    items = obj if isinstance(obj, list) else [obj]
    posts, seen = [], set()
    for item in items:
        if _is_v2_page(item):
            inc = item.get("includes") or {}
            lookup = {k: {x.get("id") or x.get("media_key"): x for x in inc.get(k, [])} for k in ("users", "places", "tweets", "media")}
            data = item["data"] if isinstance(item["data"], list) else [item["data"]]
            new = [_from_v2(t, lookup) for t in data]
        elif _is_v2_post(item):
            new = [_from_v2(item, {})]
        elif _is_v1_tweet(item):
            new = [_from_v1(item)]
        else:
            continue
        for p in new:  # pages can overlap when a search is resumed
            if p and p.post_id not in seen:
                seen.add(p.post_id)
                posts.append(p)
    return posts


def _counts(obj: dict, names: dict) -> dict[str, int]:
    return {ours: int(obj[theirs]) for theirs, ours in names.items() if isinstance(obj.get(theirs), (int, float))}


def _from_v2(t: dict, lookup: dict) -> Post | None:
    from engine.normalize import parse_time  # avoids a circular import (normalize imports the adapters)
    users, places, tweets, media = (lookup.get(k, {}) for k in ("users", "places", "tweets", "media"))
    user = users.get(t.get("author_id")) or t.get("author") or {}
    refs = {r["type"]: r["id"] for r in t.get("referenced_tweets", []) or []}
    ent = t.get("entities") or {}
    place = places.get((t.get("geo") or {}).get("place_id")) or {}
    account = t.get("author_id") or user.get("id")
    if not account or not t.get("created_at"):
        return None
    text = (t.get("note_tweet") or {}).get("text") or t.get("text") or ""  # long posts keep full text in note_tweet
    original = tweets.get(refs.get("retweeted"))
    if original:  # a repost's own text is cut short; show the original in full
        author = users.get(original.get("author_id")) or {}
        full = (original.get("note_tweet") or {}).get("text") or original.get("text") or ""
        text = f"RT @{author.get('username') or 'unknown'}: {full}"
    replied = users.get(t.get("in_reply_to_user_id")) or t.get("in_reply_to_user") or {}
    lang = t.get("lang")
    return Post(
        post_id=str(t["id"]),
        account_id=str(account),
        username=user.get("username") or str(account),
        display_name=user.get("name"),
        created_at=parse_time(t["created_at"]),
        text=text,
        repost_of=refs.get("retweeted"),
        reply_to=refs.get("replied_to"),
        quote_of=refs.get("quoted"),
        conversation_id=t.get("conversation_id"),
        reply_to_user=replied.get("username"),
        urls=[u.get("unwound_url") or u.get("expanded_url") or u.get("url") for u in ent.get("urls", []) if u],
        hashtags=[f"#{h['tag']}" for h in ent.get("hashtags", []) if h.get("tag")],
        account_created_at=parse_time(user.get("created_at")),
        followers=(user.get("public_metrics") or {}).get("followers_count"),
        verified=user.get("verified") if "verified" in user else (user.get("verified_type") not in (None, "none") or None),
        metrics=_counts(t.get("public_metrics") or {}, V2_METRICS),
        media=[media.get(k, {}).get("type", "media") for k in (t.get("attachments") or {}).get("media_keys", [])],
        platform="x",
        city=place.get("full_name") or user.get("location") or None,  # geotag if any, else the profile location
        language=None if lang in X_NO_LANGUAGE else lang,
    )


def _from_v1(t: dict) -> Post | None:
    from engine.normalize import parse_time
    user = t["user"]
    ext = t.get("extended_tweet") or {}
    ent = ext.get("entities") or t.get("entities") or {}
    ext_media = (ext.get("extended_entities") or t.get("extended_entities") or {}).get("media", [])
    created = parse_time(t.get("created_at"))
    if created is None:
        return None
    text = ext.get("full_text") or t.get("full_text") or t.get("text") or ""
    rt = t.get("retweeted_status")
    if rt:  # "RT @user: …" is cut at 140 characters; the original is embedded
        full = (rt.get("extended_tweet") or {}).get("full_text") or rt.get("full_text") or rt.get("text") or ""
        text = f"RT @{(rt.get('user') or {}).get('screen_name', 'unknown')}: {full}"
    lang = t.get("lang")
    return Post(
        post_id=t["id_str"],
        account_id=str(user.get("id_str") or user.get("id")),
        username=user.get("screen_name") or str(user.get("id_str")),
        display_name=user.get("name"),
        created_at=created,
        text=text,
        repost_of=(rt or {}).get("id_str"),
        reply_to=t.get("in_reply_to_status_id_str"),
        quote_of=t.get("quoted_status_id_str"),
        reply_to_user=t.get("in_reply_to_screen_name"),
        urls=[u.get("expanded_url") or u.get("url") for u in ent.get("urls", []) if u],
        hashtags=[f"#{h['text']}" for h in ent.get("hashtags", []) if h.get("text")],
        account_created_at=parse_time(user.get("created_at")),
        followers=user.get("followers_count"),
        verified=user.get("verified"),
        metrics=_counts(t, V1_METRICS),
        media=[m.get("type", "media") for m in ext_media],
        platform="x",
        city=(t.get("place") or {}).get("full_name") or user.get("location") or None,
        language=None if lang in X_NO_LANGUAGE else lang,
    )


# Pulling posts live from X: recent search (last 7 days). Needs a bearer token for an X API plan that includes
# search; the token is read from X_BEARER_TOKEN in src/.env and never leaves the backend.
SEARCH_URL = "https://api.x.com/2/tweets/search/recent"
SEARCH_FIELDS = {  # everything the adapter reads: authors of posts and of the posts they repost, quote or reply to
    "tweet.fields": "created_at,author_id,lang,entities,referenced_tweets,geo,conversation_id,in_reply_to_user_id,"
                    "note_tweet,public_metrics,attachments",
    "expansions": "author_id,referenced_tweets.id,referenced_tweets.id.author_id,in_reply_to_user_id,geo.place_id,"
                  "attachments.media_keys",
    "user.fields": "created_at,username,name,location,verified,verified_type,public_metrics",
    "place.fields": "full_name,country",
    "media.fields": "type",
}
X_ERRORS = {
    401: "X refused the bearer token (check X_BEARER_TOKEN in src/.env)",
    403: "This X API plan does not include search. Recent search needs a paid X API tier",
    429: "X rate limit reached. Wait about 15 minutes and try again",
}


class XApiError(Exception):
    pass


def search_recent(query: str, token: str, max_posts: int = 500, transport=None) -> list[dict]:
    """API response pages for a search query, following next_token until max_posts posts are collected."""
    import httpx
    pages, params = [], {**SEARCH_FIELDS, "query": query, "max_results": 100}
    with httpx.Client(timeout=30, transport=transport, headers={"Authorization": f"Bearer {token}"}) as client:
        while sum(len(p.get("data", [])) for p in pages) < max_posts:
            r = client.get(SEARCH_URL, params=params)
            if r.status_code != 200:
                try:
                    detail = r.json().get("detail") or r.json().get("title") or r.text[:200]
                except ValueError:
                    detail = r.text[:200]
                raise XApiError(f"{X_ERRORS.get(r.status_code, f'X API error {r.status_code}')}: {detail}")
            page = r.json()
            pages.append(page)
            if not (next_token := page.get("meta", {}).get("next_token")):
                break
            params["next_token"] = next_token
    return pages
