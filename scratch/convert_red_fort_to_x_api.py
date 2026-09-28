"""
Converts red_fort_tractor_breach_2021.json into authentic X API v2 JSON format and builds x.db
so that red-fort-2021 also conforms to the new single-input architecture!
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from engine.xstore import ingest

RAW_FILE = ROOT / "data" / "raw" / "red_fort_tractor_breach_2021.json"
RUN_DIR = ROOT / "data" / "runs" / "red-fort-2021"

posts_data = json.load(open(RAW_FILE, encoding="utf-8"))

# Build users map
users_map = {}
for p in posts_data:
    uid = p["account_id"].replace("x:", "")
    if uid not in users_map:
        users_map[uid] = {
            "id": uid,
            "username": p["username"],
            "name": p["username"].replace("_", " ").title(),
            "created_at": f"{p['account_created_at']}T00:00:00.000Z",
            "location": p.get("city", "Delhi, India"),
            "verified": False,
            "public_metrics": {"followers_count": 450, "following_count": 220, "tweet_count": 1200, "listed_count": 1}
        }

# Convert each post into X API v2 tweet object
tweets = []
for p in posts_data:
    # convert timestamp to ISO UTC string
    dt = datetime.fromisoformat(p["created_at"]).astimezone(timezone.utc)
    iso_utc = dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    pid = p["post_id"].replace("x:", "")
    uid = p["account_id"].replace("x:", "")

    raw_tags = p.get("hashtags", [])
    ht_ents = [{"start": 0, "end": len(t), "tag": t.lstrip("#")} for t in raw_tags]
    raw_urls = p.get("urls", [])
    url_ents = [{"start": 0, "end": len(u), "url": u, "expanded_url": u, "unwound_url": u, "display_url": u.replace("https://", "")} for u in raw_urls]

    t_obj = {
        "id": pid,
        "text": p["text"],
        "author_id": uid,
        "created_at": iso_utc,
        "conversation_id": pid,
        "lang": "en",
        "edit_history_tweet_ids": [pid],
        "entities": {"hashtags": ht_ents, "urls": url_ents, "mentions": []},
        "public_metrics": {
            "retweet_count": p.get("retweets", 0),
            "reply_count": p.get("replies", 0),
            "like_count": p.get("likes", 0),
            "quote_count": 0,
            "bookmark_count": 0,
            "impression_count": (p.get("likes", 0) + 1) * 25
        }
    }
    if p.get("repost_of"):
        t_obj["referenced_tweets"] = [{"type": "retweeted", "id": p["repost_of"].replace("x:", "")}]
    if p.get("reply_to"):
        t_obj["referenced_tweets"] = [{"type": "replied_to", "id": p["reply_to"].replace("x:", "")}]
    tweets.append(t_obj)

# Paginate into 100 posts per page
pages = []
page_size = 100
total = len(tweets)
num_pages = (total + page_size - 1) // page_size

for idx in range(num_pages):
    chunk = tweets[idx * page_size : min((idx + 1) * page_size, total)]
    u_ids = {t["author_id"] for t in chunk}
    inc_users = [users_map[uid] for uid in u_ids if uid in users_map]

    meta = {
        "newest_id": chunk[0]["id"],
        "oldest_id": chunk[-1]["id"],
        "result_count": len(chunk)
    }
    if idx < num_pages - 1:
        meta["next_token"] = f"token_{idx}"

    pages.append({
        "data": chunk,
        "includes": {"users": inc_users, "places": [], "media": [], "tweets": []},
        "meta": meta
    })

# Save X API v2 json
out_x_json = ROOT / "data" / "raw" / "red_fort_x_api_v2.json"
with open(out_x_json, "w", encoding="utf-8") as f:
    json.dump(pages, f, indent=2, ensure_ascii=False)

# Ingest into red-fort-2021/x.db
RUN_DIR.mkdir(parents=True, exist_ok=True)
ingest(out_x_json, RUN_DIR / "x.db")
print("Successfully converted and built x.db for red-fort-2021!")
