import ast
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from engine.schema import Post


def parse_timestamp(dt_str: str) -> int | None:
    if not dt_str or not dt_str.strip():
        return None
    dt_str = dt_str.strip()
    # Try common formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(dt_str, fmt).replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError:
            pass
    try:
        # Fallback to general fromisoformat
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def parse_list_field(val: str) -> list[str]:
    if not val or not val.strip():
        return []
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if x]
        except Exception:
            pass
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if x]
        except Exception:
            pass
    # Otherwise split by whitespace or comma
    parts = re.split(r"[\s,]+", val)
    return [p.strip() for p in parts if p.strip()]


def load_io_archive(path: str | Path, limit: int | None = None) -> list[Post]:
    posts: list[Post] = []
    with open(path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            
            if not row.get("tweet_time"):
                continue  # truncated row (our sample is a byte-range slice of the archive)
            post_id = row.get("tweetid") or f"io_{i}"
            account_id = row.get("userid") or "unknown_user"
            username = row.get("user_screen_name") or account_id
            created_at = parse_timestamp(row.get("tweet_time", "")) or 0
            text = row.get("tweet_text") or ""
            repost_of = row.get("retweet_tweetid") or None
            if repost_of == "":
                repost_of = None
            reply_to = row.get("in_reply_to_tweetid") or None
            if reply_to == "":
                reply_to = None
                
            urls = parse_list_field(row.get("urls", ""))
            hashtags = parse_list_field(row.get("hashtags", ""))
            account_created_at = parse_timestamp(row.get("account_creation_date", ""))

            posts.append(Post(
                post_id=str(post_id),
                account_id=str(account_id),
                username=str(username),
                created_at=created_at,
                text=text,
                repost_of=str(repost_of) if repost_of else None,
                reply_to=str(reply_to) if reply_to else None,
                urls=urls,
                hashtags=hashtags,
                account_created_at=account_created_at
            ))

    return posts
