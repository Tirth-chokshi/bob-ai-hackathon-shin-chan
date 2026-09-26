import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from engine.schema import Post


def parse_ira_date(dt_str: str) -> int:
    if not dt_str or not dt_str.strip():
        return 0
    dt_str = dt_str.strip()
    # Format typically: 10/1/2017 19:58 or 2017-10-01 19:58
    for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(dt_str, fmt).replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError:
            pass
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return 0


def load_ira(path: str | Path, limit: int | None = None) -> list[Post]:
    posts: list[Post] = []
    with open(path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break

            post_id = row.get("tweet_id") or f"ira_{i}"
            author = row.get("author") or row.get("external_author_id") or f"ira_author_{i}"
            account_id = str(row.get("external_author_id") or author)
            username = str(author)
            created_at = parse_ira_date(row.get("publish_date", ""))
            text = row.get("content", "")

            # URLs from tco steps and article_url
            urls = []
            for u_col in ("article_url", "tco1_step1", "tco2_step1", "tco3_step1"):
                u_val = (row.get(u_col) or "").strip()
                if u_val and u_val != "None" and u_val not in urls:
                    urls.append(u_val)

            # Extract hashtags from text
            hashtags = re.findall(r"#\w+", text)

            repost_of = None
            if row.get("retweet") == "1":
                # Marked as retweet
                repost_of = "unknown_repost"

            posts.append(Post(
                post_id=str(post_id),
                account_id=account_id,
                username=username,
                created_at=created_at,
                text=text,
                repost_of=repost_of,
                reply_to=None,
                urls=urls,
                hashtags=hashtags,
                account_created_at=None
            ))

    return posts
