import csv
import json
from pathlib import Path
from engine.schema import Post
from scenario.adapters.io_archive import load_io_archive
from scenario.adapters.ira import load_ira


def load_scenario_csv(path: str | Path, limit: int | None = None) -> list[Post]:
    posts: list[Post] = []
    with open(path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            
            urls = [u.strip() for u in (row.get("urls") or "").split() if u.strip()]
            hashtags = [h.strip() for h in (row.get("hashtags") or "").split() if h.strip()]
            
            created_at = int(row.get("created_at") or 0)
            account_created_at_raw = row.get("account_created_at")
            account_created_at = int(account_created_at_raw) if account_created_at_raw else None

            repost_of = row.get("repost_of") or None
            reply_to = row.get("reply_to") or None

            posts.append(Post(
                post_id=str(row["post_id"]),
                account_id=str(row["account_id"]),
                username=str(row["username"]),
                created_at=created_at,
                text=str(row.get("text", "")),
                repost_of=str(repost_of) if repost_of else None,
                reply_to=str(reply_to) if reply_to else None,
                urls=urls,
                hashtags=hashtags,
                account_created_at=account_created_at
            ))
    return posts


def load_posts(path: str | Path, limit: int | None = None) -> list[Post]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    # If JSON file
    if path.suffix.lower() == ".json":
        with open(path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                if limit:
                    data = data[:limit]
                return [Post.model_validate(p) for p in data]
            raise ValueError("Expected JSON array of posts")

    # If CSV, sniff the header
    with open(path, mode="r", encoding="utf-8", errors="replace") as f:
        sample = f.readline()
        columns = [c.strip().strip('"').lower() for c in sample.split(",")]

    if "tweetid" in columns and "tweet_text" in columns:
        return load_io_archive(path, limit=limit)
    elif ("tweet_id" in columns or "author" in columns) and "publish_date" in columns:
        return load_ira(path, limit=limit)
    elif "post_id" in columns and "account_id" in columns:
        return load_scenario_csv(path, limit=limit)
    else:
        # Fallback to standard scenario format
        return load_scenario_csv(path, limit=limit)
