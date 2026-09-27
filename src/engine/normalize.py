"""Turns an uploaded CSV/JSON into Posts. Format guide for users: docs/data-format.md."""
import csv
import hashlib
import itertools
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from engine.schema import Post
from scenario.adapters.io_archive import load_io_archive, parse_list_field
from scenario.adapters.ira import load_ira

log = logging.getLogger(__name__)

# Accepted column names per field, compared after lower-casing and turning spaces/dashes into "_"
ALIASES = {
    "post_id": ["post_id", "id", "tweet_id", "tweetid", "status_id", "message_id", "unique_id"],
    "account_id": ["account_id", "user_id", "userid", "author_id", "account", "user", "author", "username", "screen_name", "handle"],
    "username": ["username", "screen_name", "user_screen_name", "handle", "author", "user", "account"],
    "created_at": ["created_at", "timestamp", "time", "date", "datetime", "tweet_time", "posted_at", "publish_date"],
    "text": ["text", "content", "message", "post", "tweet", "tweet_text", "body"],
    "urls": ["urls", "url", "links", "link"],
    "hashtags": ["hashtags", "hashtag", "tags"],
    "reply_to": ["reply_to", "in_reply_to", "in_reply_to_id", "in_reply_to_status_id", "in_reply_to_tweetid", "parent_id"],
    "repost_of": ["repost_of", "retweet_of", "retweet_id", "retweet_tweetid", "retweeted_status_id", "shared_post_id"],
    "account_created_at": ["account_created_at", "account_creation_date", "user_created_at"],
}
REQUIRED = {"account_id": "who posted it", "created_at": "when it was posted", "text": "what it says"}
TIME_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
                "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%a %b %d %H:%M:%S %z %Y"]
URL_RE = re.compile(r"https?://\S+")
HASHTAG_RE = re.compile(r"#\w+")


def parse_time(value) -> int | None:
    """Unix seconds from epoch seconds/milliseconds or a date string; times without a zone are taken as UTC."""
    v = str(value if value is not None else "").strip()
    if not v:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", v):
        t = float(v)
        return int(t / 1000 if t > 1e11 else t)  # 13-digit values are milliseconds
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        for fmt in TIME_FORMATS:
            try:
                dt = datetime.strptime(v, fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def as_list(value) -> list[str]:
    return [str(x) for x in value if x] if isinstance(value, list) else parse_list_field(str(value or ""))


def column_key(name: str) -> str:
    return re.sub(r"[\s\-]+", "_", name.strip().lower())


def load_rows(rows, columns: list[str], source_name: str | None = None,
              source_id: str | None = None) -> list[Post]:
    """Map rows (dicts) with any of the accepted column names onto Posts."""
    keys = {c: column_key(c) for c in columns}
    col = {field: next((c for name in names for c in columns if keys[c] == name), None) for field, names in ALIASES.items()}

    missing = [f for f in REQUIRED if not col[f]]
    if missing:
        need = "; ".join(f"{REQUIRED[f]} (e.g. {' / '.join(ALIASES[f][:4])})" for f in missing)
        hint = (" The engine finds campaigns from who posted what and when, so a text-only dataset can't be analysed."
                if col["text"] else "")
        raise ValueError(f"Missing columns for {need}. Found: {', '.join(columns)}.{hint} "
                         "See docs/data-format.md or download the template.")

    posts, skipped = [], 0
    ingested_at = int(datetime.now(timezone.utc).timestamp())
    for i, row in enumerate(rows):
        def get(field):
            return row.get(col[field]) if col[field] else None

        account = str(get("account_id") or "").strip()
        created_at = parse_time(get("created_at"))
        if not account or created_at is None:
            skipped += 1
            continue
        text = str(get("text") or "")
        raw_post = {
            "post_id": str(get("post_id") or f"row{i + 1}"),
            "account_id": account,
            "username": str(get("username") or account),
            "created_at": created_at,
            "text": text,
            "repost_of": str(get("repost_of") or "").strip() or None,
            "reply_to": str(get("reply_to") or "").strip() or None,
            # no column (or empty): take links and hashtags from the text
            "urls": as_list(get("urls")) or URL_RE.findall(text),
            "hashtags": as_list(get("hashtags")) or HASHTAG_RE.findall(text),
            "account_created_at": parse_time(get("account_created_at")),
        }
        origins = {
            "post_id": "supplied" if get("post_id") else "defaulted",
            "account_id": "supplied",
            "username": "supplied" if get("username") else "defaulted",
            "created_at": "supplied",
            "text": "supplied",
            "repost_of": "supplied" if get("repost_of") else "defaulted",
            "reply_to": "supplied" if get("reply_to") else "defaulted",
            "urls": "supplied" if as_list(get("urls")) else "extracted" if URL_RE.search(text) else "defaulted",
            "hashtags": "supplied" if as_list(get("hashtags")) else "extracted" if HASHTAG_RE.search(text) else "defaulted",
            "account_created_at": "supplied" if get("account_created_at") else "defaulted",
        }
        original_hash = hashlib.sha256(
            json.dumps(row, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        post = Post(**raw_post, source_id=source_id, source_name=source_name, source_row=i + 1,
                    ingested_at=ingested_at, original_record_sha256=original_hash, field_origins=origins)
        normalized_hash = hashlib.sha256(
            json.dumps(post.model_dump(exclude={"normalized_record_sha256"}), sort_keys=True,
                       ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        posts.append(post.model_copy(update={"normalized_record_sha256": normalized_hash}))

    if not posts:
        raise ValueError(f"No usable rows: all {skipped} rows lack an account or a readable time "
                         f"(time column '{col['created_at']}'). See docs/data-format.md for accepted time formats.")
    if skipped:
        log.warning("Skipped %d rows without an account or a readable time", skipped)
    return posts


def load_posts(path: str | Path, limit: int | None = None) -> list[Post]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
            raise ValueError("Expected a JSON array of post objects")
        rows = data[:limit] if limit else data
        return load_rows(rows, list(dict.fromkeys(k for r in rows for k in r)), path.name, path.parent.name)

    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        try:  # comma, semicolon (Excel in many locales) or tab
            dialect = csv.Sniffer().sniff(f.read(64 * 1024), delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
        columns = reader.fieldnames or []
        names = {column_key(c) for c in columns}

        # Known research archives need their own handling (retweet fields, rounded IDs)
        if {"tweetid", "tweet_text"} <= names:
            return load_io_archive(path, limit=limit)
        if "publish_date" in names and ("author" in names or "tweet_id" in names):
            return load_ira(path, limit=limit)
        return load_rows(itertools.islice(reader, limit) if limit else reader, columns, path.name, path.parent.name)
