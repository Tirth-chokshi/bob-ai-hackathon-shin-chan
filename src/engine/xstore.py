"""The only input format, and how it is stored. Full description: docs/data-model.md.

INPUT: X API v2 JSON exactly as the API returns it, in a .json or .jsonl file:
  - one response page  {"data": [post, ...], "includes": {"users", "tweets", "places", "media"}, "meta": {...}}
    (recent / full-archive search, user timelines, quote and retweet lookups, post lookup)
  - a list of such pages, or one page per line (.jsonl)
  - filtered-stream output: one {"data": {post}, "includes": ..., "matching_rules": [...]} per line
Anything else (v1.1 tweets, CSV, other platforms, hand-made shapes) is refused with the reason.

STORAGE: one SQLite database per dataset, data/runs/<id>/x.db. One table per X API object, columns named as in the
X API data dictionary (https://docs.x.com/x-api/fundamentals/data-dictionary). The analysis reads the `posts` view,
the single place where X fields are mapped onto what the engine uses.
"""
import json
import re
import sqlite3
from pathlib import Path

from engine.schema import Post

# The request fields that give the engine everything it uses. created_at and author_id are the minimum.
REQUIRED_POST_FIELDS = ("id", "text", "created_at", "author_id")
RECOMMENDED_REQUEST = {
    "tweet.fields": "created_at,author_id,conversation_id,in_reply_to_user_id,referenced_tweets,entities,lang,"
                    "public_metrics,geo,attachments,note_tweet",
    "expansions": "author_id,referenced_tweets.id,referenced_tweets.id.author_id,in_reply_to_user_id,geo.place_id,"
                  "attachments.media_keys",
    "user.fields": "created_at,username,name,location,description,verified,verified_type,public_metrics",
    "place.fields": "full_name,name,country,country_code,place_type",
    "media.fields": "type,url,preview_image_url,alt_text",
}
NO_LANGUAGE = {"und", "qme", "zxx", "qht", "qam", "qct", "qst"}  # X's codes for "no linguistic content"

SCHEMA = """
-- Posts: `data` of each response (source = 'data') and the referenced posts in `includes.tweets` (source = 'includes',
-- shown for context, not analysed). One column per post field; public_metrics and note_tweet are flattened.
CREATE TABLE IF NOT EXISTS tweets (
    id                   TEXT PRIMARY KEY,
    source               TEXT NOT NULL CHECK (source IN ('data', 'includes')),
    text                 TEXT NOT NULL,
    note_tweet_text      TEXT,              -- note_tweet.text: full text of posts over 280 characters
    author_id            TEXT,
    created_at           TEXT,              -- ISO 8601, as returned
    conversation_id      TEXT,
    in_reply_to_user_id  TEXT,
    lang                 TEXT,
    possibly_sensitive   INTEGER,
    geo_place_id         TEXT,              -- geo.place_id
    retweet_count        INTEGER,           -- public_metrics.*
    reply_count          INTEGER,
    like_count           INTEGER,
    quote_count          INTEGER,
    bookmark_count       INTEGER,
    impression_count     INTEGER
);
-- referenced_tweets: [{type, id}] of each post
CREATE TABLE IF NOT EXISTS referenced_tweets (
    tweet_id  TEXT NOT NULL REFERENCES tweets(id),
    type      TEXT NOT NULL CHECK (type IN ('retweeted', 'quoted', 'replied_to')),
    id        TEXT NOT NULL,
    PRIMARY KEY (tweet_id, type, id)
);
-- entities.hashtags / entities.urls / entities.mentions
CREATE TABLE IF NOT EXISTS entities_hashtags (tweet_id TEXT NOT NULL, tag TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entities_urls (tweet_id TEXT NOT NULL, url TEXT, expanded_url TEXT, unwound_url TEXT);
CREATE TABLE IF NOT EXISTS entities_mentions (tweet_id TEXT NOT NULL, username TEXT, id TEXT);
-- attachments.media_keys
CREATE TABLE IF NOT EXISTS attachments_media (tweet_id TEXT NOT NULL, media_key TEXT NOT NULL);
-- includes.users; public_metrics flattened
CREATE TABLE IF NOT EXISTS users (
    id               TEXT PRIMARY KEY,
    username         TEXT NOT NULL,
    name             TEXT,
    created_at       TEXT,
    location         TEXT,
    description      TEXT,
    verified         INTEGER,
    verified_type    TEXT,
    followers_count  INTEGER,
    following_count  INTEGER,
    tweet_count      INTEGER,
    listed_count     INTEGER
);
-- includes.places
CREATE TABLE IF NOT EXISTS places (id TEXT PRIMARY KEY, full_name TEXT, name TEXT, country TEXT, country_code TEXT,
                                   place_type TEXT);
-- includes.media
CREATE TABLE IF NOT EXISTS media (media_key TEXT PRIMARY KEY, type TEXT, url TEXT, preview_image_url TEXT, alt_text TEXT);
-- matching_rules of filtered-stream lines
CREATE TABLE IF NOT EXISTS matching_rules (tweet_id TEXT NOT NULL, id TEXT, tag TEXT);
-- meta of each response page, and the page's errors (X returns partial results with "errors")
CREATE TABLE IF NOT EXISTS responses (n INTEGER PRIMARY KEY, meta TEXT, errors TEXT);

-- What the analysis reads: one row per post in `data`, X fields mapped onto the engine's names
CREATE VIEW IF NOT EXISTS posts AS
SELECT t.id                                      AS post_id,
       t.author_id                               AS account_id,
       COALESCE(u.username, t.author_id)         AS username,
       u.name                                    AS display_name,
       t.created_at                              AS created_at,
       COALESCE(t.note_tweet_text, t.text)       AS text,
       (SELECT id FROM referenced_tweets r WHERE r.tweet_id = t.id AND r.type = 'retweeted')  AS repost_of,
       (SELECT id FROM referenced_tweets r WHERE r.tweet_id = t.id AND r.type = 'replied_to') AS reply_to,
       (SELECT id FROM referenced_tweets r WHERE r.tweet_id = t.id AND r.type = 'quoted')     AS quote_of,
       t.conversation_id                         AS conversation_id,
       ru.username                               AS reply_to_user,
       u.created_at                              AS account_created_at,
       u.followers_count                         AS followers,
       COALESCE(u.verified, CASE WHEN u.verified_type IS NULL THEN NULL
                                 ELSE u.verified_type NOT IN ('none', '') END) AS verified,
       COALESCE(p.full_name, u.location)         AS city,
       t.lang                                    AS language,
       t.like_count, t.retweet_count, t.reply_count, t.quote_count, t.impression_count
FROM tweets t
LEFT JOIN users u  ON u.id = t.author_id
LEFT JOIN users ru ON ru.id = t.in_reply_to_user_id
LEFT JOIN places p ON p.id = t.geo_place_id
WHERE t.source = 'data';
"""


class NotXApiData(ValueError):
    """The file is not X API v2 output, or lacks fields the analysis needs."""


def read_file(path: Path) -> list[dict]:
    """The response objects in a .json (one object or a list) or .jsonl (one object per line) file."""
    text = Path(path).read_text(encoding="utf-8-sig")
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        try:
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        except json.JSONDecodeError as e:
            raise NotXApiData(f"Not valid JSON or JSON Lines ({e.msg}, line {e.lineno})") from None


def check(responses: list[dict]) -> list[str]:
    """Refuses anything that isn't X API v2 output with the reason; returns warnings for missing recommended fields."""
    if not responses:
        raise NotXApiData("The file is empty")
    for i, r in enumerate(responses):
        where = f"object {i + 1}" if len(responses) > 1 else "the file"
        if not isinstance(r, dict):
            raise NotXApiData(f"{where} is not a JSON object. Upload X API v2 responses as returned by the API.")
        if "id_str" in r or "user" in r:
            raise NotXApiData(f"{where} looks like X API v1.1 data (id_str, user). Only X API v2 responses are accepted.")
        if "data" not in r and "meta" not in r and "errors" not in r:
            raise NotXApiData(f"{where} has no \"data\": it is not an X API v2 response. Expected "
                              "{\"data\": [...], \"includes\": {...}, \"meta\": {...}} as returned by the API.")
    posts = [t for r in responses for t in _as_list(r.get("data"))]
    if not posts:
        raise NotXApiData("The responses contain no posts (\"data\" is empty)")
    missing = {f: sum(1 for t in posts if not isinstance(t, dict) or not t.get(f)) for f in REQUIRED_POST_FIELDS}
    if any(missing.values()):
        need = ", ".join(f"{n} without {f}" for f, n in missing.items() if n)
        raise NotXApiData(f"{need} (of {len(posts)} posts). Request them with tweet.fields=created_at,author_id; "
                          "they are needed to see who posted what, and when.")
    bad_time = sum(1 for t in posts if not _is_iso(t["created_at"]))
    if bad_time:
        raise NotXApiData(f"{bad_time} posts have a created_at that is not ISO 8601 (X returns 2021-01-26T10:15:00.000Z)")

    users = {u.get("id") for r in responses for u in (r.get("includes") or {}).get("users", [])}
    warnings = []
    no_author = sum(1 for t in posts if t["author_id"] not in users)
    if no_author:
        warnings.append(f"{no_author} posts have no author in includes.users, so usernames and account ages are "
                        "missing (add expansions=author_id and user.fields=created_at,username)")
    if not any("public_metrics" in t for t in posts):
        warnings.append("No public_metrics: like, repost and reply counts will not be shown (add tweet.fields=public_metrics)")
    if not any("referenced_tweets" in t for t in posts):
        warnings.append("No referenced_tweets: reposts, replies and quotes can't be linked (add tweet.fields=referenced_tweets)")
    return warnings


def build(responses: list[dict], db_path: Path | str) -> sqlite3.Connection:
    """Checked responses into a database (":memory:" for a throwaway one). Posts seen twice are stored once."""
    db = sqlite3.connect(str(db_path))
    db.executescript(SCHEMA)
    with db:
        for n, r in enumerate(responses):
            inc = r.get("includes") or {}
            for u in inc.get("users", []):
                m = u.get("public_metrics") or {}
                db.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                           (str(u["id"]), u.get("username") or str(u["id"]), u.get("name"), u.get("created_at"),
                            u.get("location"), u.get("description"), _bool(u.get("verified")), u.get("verified_type"),
                            m.get("followers_count"), m.get("following_count"), m.get("tweet_count"), m.get("listed_count")))
            for p in inc.get("places", []):
                db.execute("INSERT OR REPLACE INTO places VALUES (?,?,?,?,?,?)",
                           (str(p["id"]), p.get("full_name"), p.get("name"), p.get("country"), p.get("country_code"),
                            p.get("place_type")))
            for m in inc.get("media", []):
                db.execute("INSERT OR REPLACE INTO media VALUES (?,?,?,?,?)",
                           (m["media_key"], m.get("type"), m.get("url"), m.get("preview_image_url"), m.get("alt_text")))
            for t in inc.get("tweets", []):
                _insert_post(db, t, "includes")
            for t in _as_list(r.get("data")):
                _insert_post(db, t, "data")
                for rule in r.get("matching_rules", []):
                    db.execute("INSERT INTO matching_rules VALUES (?,?,?)", (str(t["id"]), rule.get("id"), rule.get("tag")))
            db.execute("INSERT INTO responses VALUES (?,?,?)", (n, json.dumps(r.get("meta")), json.dumps(r.get("errors"))))
    return db


def _insert_post(db: sqlite3.Connection, t: dict, source: str):
    pid = str(t["id"])
    if source == "includes" and db.execute("SELECT 1 FROM tweets WHERE id = ?", (pid,)).fetchone():
        return  # a post already stored (in `data` or earlier includes) stays as it is
    m = t.get("public_metrics") or {}
    db.execute("DELETE FROM tweets WHERE id = ?", (pid,))  # a post seen twice (overlapping pages) is stored once
    for table in ("referenced_tweets", "entities_hashtags", "entities_urls", "entities_mentions", "attachments_media"):
        db.execute(f"DELETE FROM {table} WHERE tweet_id = ?", (pid,))
    db.execute("INSERT INTO tweets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (pid, source, t.get("text") or "", (t.get("note_tweet") or {}).get("text"),
                _str(t.get("author_id")), t.get("created_at"), _str(t.get("conversation_id")),
                _str(t.get("in_reply_to_user_id")), t.get("lang"), _bool(t.get("possibly_sensitive")),
                (t.get("geo") or {}).get("place_id"), m.get("retweet_count"), m.get("reply_count"), m.get("like_count"),
                m.get("quote_count"), m.get("bookmark_count"), m.get("impression_count")))
    for ref in t.get("referenced_tweets") or []:
        db.execute("INSERT OR IGNORE INTO referenced_tweets VALUES (?,?,?)", (pid, ref["type"], str(ref["id"])))
    ent = t.get("entities") or {}
    db.executemany("INSERT INTO entities_hashtags VALUES (?,?)", [(pid, h["tag"]) for h in ent.get("hashtags", []) if h.get("tag")])
    db.executemany("INSERT INTO entities_urls VALUES (?,?,?,?)",
                   [(pid, u.get("url"), u.get("expanded_url"), u.get("unwound_url")) for u in ent.get("urls", [])])
    db.executemany("INSERT INTO entities_mentions VALUES (?,?,?)",
                   [(pid, m.get("username"), _str(m.get("id"))) for m in ent.get("mentions", [])])
    db.executemany("INSERT INTO attachments_media VALUES (?,?)",
                   [(pid, k) for k in (t.get("attachments") or {}).get("media_keys", [])])


# The referenced posts from includes.tweets, in the same columns as the posts view (shown for context only)
_INCLUDED_POSTS = """
SELECT t.id AS post_id, t.author_id AS account_id, COALESCE(u.username, t.author_id) AS username, u.name AS display_name,
       t.created_at, COALESCE(t.note_tweet_text, t.text) AS text,
       (SELECT id FROM referenced_tweets r WHERE r.tweet_id = t.id AND r.type = 'retweeted')  AS repost_of,
       (SELECT id FROM referenced_tweets r WHERE r.tweet_id = t.id AND r.type = 'replied_to') AS reply_to,
       (SELECT id FROM referenced_tweets r WHERE r.tweet_id = t.id AND r.type = 'quoted')     AS quote_of,
       t.conversation_id, NULL AS reply_to_user, u.created_at AS account_created_at, u.followers_count AS followers,
       u.verified, u.location AS city, t.lang AS language,
       t.like_count, t.retweet_count, t.reply_count, t.quote_count, t.impression_count
FROM tweets t LEFT JOIN users u ON u.id = t.author_id
WHERE t.source = 'includes' AND t.created_at IS NOT NULL
"""


def read_posts(db: sqlite3.Connection, source: str = "data") -> list[Post]:
    """The engine's posts: the `posts` view (source="data"), or the context posts from includes.tweets
    (source="includes"), with each post's hashtags, links and media types. A repost's text is the reposted post in
    full ("RT @user: <full text>") when X included the original."""
    from engine.normalize import HASHTAG_RE, URL_RE, detect_language, parse_time  # normalize imports nothing from here
    db.row_factory = sqlite3.Row
    hashtags = _group(db.execute("SELECT tweet_id, '#' || tag FROM entities_hashtags"))
    urls = _group(db.execute("SELECT tweet_id, COALESCE(unwound_url, expanded_url, url) FROM entities_urls"))
    media = _group(db.execute("SELECT a.tweet_id, COALESCE(m.type, 'media') FROM attachments_media a "
                              "LEFT JOIN media m USING (media_key)"))
    originals = {r["id"]: f"RT @{r['username'] or 'unknown'}: {r['full']}" for r in db.execute(
        "SELECT t.id, u.username, COALESCE(t.note_tweet_text, t.text) AS full FROM tweets t LEFT JOIN users u ON u.id = t.author_id")}
    posts = []
    for r in db.execute("SELECT * FROM posts" if source == "data" else _INCLUDED_POSTS):
        pid = r["post_id"]
        text = originals[r["repost_of"]] if r["repost_of"] in originals else r["text"]
        metrics = {k: r[col] for k, col in (("likes", "like_count"), ("reposts", "retweet_count"), ("replies", "reply_count"),
                                            ("quotes", "quote_count"), ("views", "impression_count")) if r[col] is not None}
        posts.append(Post(
            post_id=pid, account_id=r["account_id"] or "unknown", username=r["username"] or "unknown",
            display_name=r["display_name"], created_at=parse_time(r["created_at"]), text=text,
            repost_of=r["repost_of"], reply_to=r["reply_to"], quote_of=r["quote_of"],
            conversation_id=r["conversation_id"], reply_to_user=r["reply_to_user"],
            account_created_at=parse_time(r["account_created_at"]), followers=r["followers"],
            verified=None if r["verified"] is None else bool(r["verified"]), city=r["city"], platform="x",
            language=r["language"] if r["language"] and r["language"] not in NO_LANGUAGE else detect_language(text),
            # entities when requested; otherwise the links and hashtags in the text X returned
            urls=urls.get(pid) or URL_RE.findall(text), hashtags=hashtags.get(pid) or HASHTAG_RE.findall(text),
            media=media.get(pid, []), metrics=metrics,
        ))
    posts.sort(key=lambda p: (p.created_at, p.post_id))
    return posts


def ingest(path: Path, db_path: Path) -> tuple[list[Post], list[str]]:
    """An uploaded file checked and stored in db_path; returns the posts to analyse and any warnings."""
    responses = read_file(path)
    warnings = check(responses)
    Path(db_path).unlink(missing_ok=True)
    db = build(responses, db_path)
    try:
        return read_posts(db), warnings
    finally:
        db.close()


def posts_from_responses(responses: list[dict]) -> list[Post]:
    """Checked responses straight to posts, through an in-memory database (the stream API, tests)."""
    check(responses)
    db = build(responses, ":memory:")
    try:
        return read_posts(db)
    finally:
        db.close()


def load_posts(path: Path) -> list[Post]:
    """The posts of an X API v2 file, without keeping a database."""
    return posts_from_responses(read_file(path))


def open_db(run_dir: Path) -> sqlite3.Connection:
    path = Path(run_dir) / "x.db"
    if not path.exists():
        raise FileNotFoundError("This dataset has no X database. Upload it again as X API v2 JSON.")
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def _as_list(v) -> list:
    return v if isinstance(v, list) else [v] if isinstance(v, dict) else []


def _group(rows) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for tweet_id, value in rows:
        if value:
            out.setdefault(tweet_id, []).append(value)
    return out


def _str(v):
    return None if v is None else str(v)


def _bool(v):
    return None if v is None else int(bool(v))


def _is_iso(v) -> bool:
    return isinstance(v, str) and bool(re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", v))
