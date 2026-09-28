"""Test data in the only accepted input format: X API v2 responses. Built at test time; never stored or shown in the app.

planted_response(): one search response page with
- 120 ordinary accounts, each posting its own text at random times over six hours
- ring "R": 10 accounts a few days old post the same text and link within seconds, four times
- ring "H": 8 accounts reply to the same post within minutes, three times (a pile-on)
"""
import json
import random
from datetime import datetime, timezone
from pathlib import Path

T0 = 1790000000  # a fixed start time, so every run is the same
WORDS = "rain market school bus road water power price train match film exam temple crowd news phone".split()


def iso(t: int) -> str:
    """Unix seconds as X writes created_at: 2026-09-21T10:13:20.000Z"""
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def x_post(pid: str, author: str, t: int, text: str, **fields) -> dict:
    """A post object as X API v2 returns it with tweet.fields=created_at,author_id,lang,entities,referenced_tweets."""
    post = {"id": pid, "text": text, "author_id": author, "created_at": iso(t), "edit_history_tweet_ids": [pid]}
    return {**post, **fields}


def planted_response(seed: int = 7) -> tuple[dict, dict]:
    r = random.Random(seed)
    posts, users, n = [], [], iter(range(1_300_000_000_000_000_000, 1_400_000_000_000_000_000))
    user = lambda uid, username, created: users.append({"id": uid, "username": username, "name": username.title(),
                                                        "created_at": iso(created)})

    organic = [str(2_000_000 + i) for i in range(120)]
    for i, a in enumerate(organic):
        user(a, f"citizen_{i}", T0 - 3 * 365 * 86400)
        for k in range(3):
            posts.append(x_post(str(next(n)), a, T0 + r.randint(0, 6 * 3600), " ".join(r.sample(WORDS, 6)) + f" {i}-{k}", lang="en"))

    ring = [str(3_000_000 + i) for i in range(10)]
    for i, a in enumerate(ring):
        user(a, f"alert_{i}", T0 - 3 * 86400)
    for burst in range(4):
        start = T0 + 3600 + burst * 1800
        for a in ring:
            posts.append(x_post(str(next(n)), a, start + r.randint(0, 40),
                                "Bus stand pe sab log pahuncho aaj shaam 6 baje https://t.co/k7 #RajpuraBachao", lang="hi",
                                entities={"urls": [{"url": "https://t.co/k7", "expanded_url": "https://youtu.be/k7Xq2ZtR9dA"}],
                                          "hashtags": [{"tag": "RajpuraBachao"}]}))

    pile = [str(4_000_000 + i) for i in range(8)]
    for i, a in enumerate(pile):
        user(a, f"troll_{i}", T0 - 10 * 86400)
    user("999", "factcheck", T0 - 5 * 365 * 86400)
    for burst in range(3):
        start, target = T0 + 2 * 3600 + burst * 2400, str(1_200_000_000_000_000_000 + burst)
        for a in pile:
            posts.append(x_post(str(next(n)), a, start + r.randint(0, 200), f"@factcheck jhooth mat bolo {r.choice(WORDS)} #Resign",
                                lang="hi", in_reply_to_user_id="999", conversation_id=target,
                                referenced_tweets=[{"type": "replied_to", "id": target}],
                                entities={"hashtags": [{"tag": "Resign"}], "mentions": [{"username": "factcheck", "id": "999"}]}))

    posts.sort(key=lambda p: p["created_at"])
    response = {"data": posts, "includes": {"users": users}, "meta": {"result_count": len(posts)}}
    return response, {"R": ring, "H": pile, "organic": organic}


def write_json(path: Path, response) -> Path:
    path.write_text(json.dumps(response, ensure_ascii=False), encoding="utf-8")
    return path


# A search page with every field the adapter reads: a repost whose original is in includes.tweets, a reply to a user
# in includes.users, a quote with a photo, public_metrics, verified, places.
X_PAGE = {
    "data": [
        {"id": "1308", "author_id": "u1", "created_at": "2020-09-22T04:32:00.000Z", "lang": "hi",
         "text": "RT @orig: राजपुरा बस स्टैंड #बच्चा_चोर", "referenced_tweets": [{"type": "retweeted", "id": "1300"}],
         "conversation_id": "1300", "public_metrics": {"retweet_count": 41, "reply_count": 0, "like_count": 0,
                                                       "quote_count": 0, "impression_count": 0},
         "entities": {"hashtags": [{"start": 20, "end": 30, "tag": "बच्चा_चोर"}],
                      "urls": [{"url": "https://t.co/x", "expanded_url": "https://youtu.be/k7"}]}},
        {"id": "1309", "author_id": "u2", "created_at": "2020-09-22T04:33:00.000Z", "lang": "und",
         "text": "@NavgarhPolice short text…", "note_tweet": {"text": "@NavgarhPolice the full long text"},
         "referenced_tweets": [{"type": "replied_to", "id": "1301"}], "in_reply_to_user_id": "u9",
         "conversation_id": "1301", "geo": {"place_id": "p1"}},
        {"id": "1310", "author_id": "u2", "created_at": "2020-09-22T04:40:00.000Z", "lang": "en",
         "text": "Is this true? https://t.co/q", "referenced_tweets": [{"type": "quoted", "id": "1300"}],
         "attachments": {"media_keys": ["3_1"]},
         "public_metrics": {"retweet_count": 2, "reply_count": 5, "like_count": 17, "quote_count": 1,
                            "impression_count": 940}},
    ],
    "includes": {
        "users": [{"id": "u1", "username": "alert_rahul", "name": "Rahul", "created_at": "2020-09-19T10:00:00.000Z",
                   "location": "Rajpura", "verified": False, "public_metrics": {"followers_count": 12}},
                  {"id": "u2", "username": "jago_91", "name": "Jago", "created_at": "2016-01-01T00:00:00.000Z",
                   "verified_type": "blue"},
                  {"id": "u3", "username": "orig", "name": "Original Author", "created_at": "2015-01-01T00:00:00.000Z"},
                  {"id": "u9", "username": "NavgarhPolice", "name": "Navgarh Police"}],
        "tweets": [{"id": "1300", "author_id": "u3", "created_at": "2020-09-22T04:00:00.000Z",
                    "text": "राजपुरा बस स्टैंड के पास बच्चा चोर गिरोह घूम रहा है, पूरा संदेश"}],
        "places": [{"id": "p1", "full_name": "Navgarh, India"}],
        "media": [{"media_key": "3_1", "type": "photo"}],
    },
    "meta": {"result_count": 3, "next_token": "abc"},
}
