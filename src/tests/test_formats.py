"""Files people actually have: X API responses, JSON Lines, nested JSON, Excel, CSVs with their own column names."""
import json

import pytest

from engine.normalize import MissingColumns, load_posts, preview, suggest_mapping

X_PAGE = {  # GET /2/tweets/search/recent with the fields and expansions in x_api.SEARCH_FIELDS
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
                  {"id": "u3", "username": "orig", "name": "Original Author"},
                  {"id": "u9", "username": "NavgarhPolice", "name": "Navgarh Police"}],
        "tweets": [{"id": "1300", "author_id": "u3", "text": "राजपुरा बस स्टैंड के पास बच्चा चोर गिरोह घूम रहा है, पूरा संदेश"}],
        "places": [{"id": "p1", "full_name": "Navgarh, India"}],
        "media": [{"media_key": "3_1", "type": "photo"}],
    },
    "meta": {"result_count": 3, "next_token": "abc"},
}


def test_x_api_page(tmp_path):
    f = tmp_path / "search.json"
    f.write_text(json.dumps(X_PAGE, ensure_ascii=False), encoding="utf-8")
    a, b, c = load_posts(f)
    assert (a.account_id, a.username, a.display_name, a.platform, a.repost_of, a.city) == \
        ("u1", "alert_rahul", "Rahul", "x", "1300", "Rajpura")
    assert a.text == "RT @orig: राजपुरा बस स्टैंड के पास बच्चा चोर गिरोह घूम रहा है, पूरा संदेश"  # full original, not cut short
    assert a.hashtags == ["#बच्चा_चोर"] and a.urls == ["https://youtu.be/k7"] and a.account_created_at == 1600509600
    assert (a.followers, a.verified, a.metrics["reposts"], a.conversation_id) == (12, False, 41, "1300")
    assert b.text == "@NavgarhPolice the full long text" and b.reply_to == "1301" and b.city == "Navgarh, India"
    assert b.reply_to_user == "NavgarhPolice" and b.verified is True and b.language != "und"
    assert (c.quote_of, c.media, c.metrics) == ("1300", ["photo"], {"likes": 17, "reposts": 2, "replies": 5,
                                                                   "quotes": 1, "views": 940})


def test_x_stream_and_twarc_jsonl(tmp_path):
    # filtered stream: one {"data": {...}, "includes", "matching_rules"} per line; the same post twice is kept once
    line = lambda i: json.dumps({"data": {**X_PAGE["data"][0], "id": str(i)}, "includes": X_PAGE["includes"],
                                 "matching_rules": [{"id": "1", "tag": "rumour"}]}, ensure_ascii=False)
    f = tmp_path / "stream.jsonl"
    f.write_text("\n".join([line(1), line(2), line(2)]), encoding="utf-8")
    assert [p.post_id for p in load_posts(f)] == ["1", "2"]


def test_x_v1_tweets(tmp_path):
    f = tmp_path / "tweets.json"
    f.write_text(json.dumps([{
        "id_str": "9", "created_at": "Tue Sep 22 04:32:00 +0000 2020", "full_text": "same text #Rajpura",
        "user": {"id_str": "77", "screen_name": "abc", "created_at": "Sat Sep 19 10:00:00 +0000 2020"},
        "retweeted_status": {"id_str": "5", "full_text": "the whole original #Rajpura", "user": {"screen_name": "src"}},
        "entities": {"hashtags": [{"text": "Rajpura"}], "urls": []}, "retweet_count": 40, "favorite_count": 0,
        "quoted_status_id_str": "4", "in_reply_to_screen_name": None,
    }]), encoding="utf-8")
    [p] = load_posts(f)
    assert (p.post_id, p.account_id, p.username, p.repost_of, p.hashtags) == ("9", "77", "abc", "5", ["#Rajpura"])
    assert p.text == "RT @src: the whole original #Rajpura" and p.metrics == {"likes": 0, "reposts": 40}
    assert p.quote_of == "4"


def test_nested_json_and_own_column_names(tmp_path):
    f = tmp_path / "export.json"
    f.write_text(json.dumps({"posts": [
        {"id": "a", "created": "2020-09-22 10:00", "user": {"screen_name": "x"}, "body": "hello there"},
    ]}), encoding="utf-8")
    [p] = load_posts(f)  # nested user.screen_name matches user_screen_name
    assert (p.post_id, p.account_id, p.text) == ("a", "x", "hello there")


def test_columns_guessed_from_values_or_mapped_by_the_user(tmp_path):
    f = tmp_path / "messy.csv"
    rows = ["Sr,Poster,When posted,Message body,Likes"] + [
        f"{i},{['ramesh', 'pintu', 'meena'][i % 3]},22/09/2020 10:{i:02d},aaj shaam sab log bus stand pahuncho {i},{i * 3}"
        for i in range(12)]
    f.write_text("\n".join(rows), encoding="utf-8")
    with pytest.raises(MissingColumns):  # names say nothing, so the upload asks
        load_posts(f)
    guess = preview(f)["suggested"]
    assert (guess["account_id"], guess["created_at"], guess["text"]) == ("Poster", "When posted", "Message body")
    posts = load_posts(f, mapping=guess)
    assert len(posts) == 12 and posts[0].account_id == "ramesh" and posts[0].language == "hinglish"


def test_excel(tmp_path):
    from datetime import datetime
    from openpyxl import Workbook
    book = Workbook()
    book.active.append(["user_id", "timestamp", "text"])
    book.active.append(["a1", datetime(2020, 9, 22, 10, 0), "first post"])
    book.save(tmp_path / "posts.xlsx")
    [p] = load_posts(tmp_path / "posts.xlsx")
    assert (p.account_id, p.created_at, p.text) == ("a1", 1600768800, "first post")


def test_value_guess_ignores_counts_and_ids():
    sample = [{"likes": str(i), "at": f"2020-09-22T10:{i:02d}:00Z", "who": "a" if i % 2 else "b",
               "words": "a long enough message body"} for i in range(10)]
    m = suggest_mapping(["likes", "at", "who", "words"], sample)
    assert (m["created_at"], m["account_id"], m["text"]) == ("at", "who", "words")


def test_x_recent_search_follows_next_token():
    import httpx
    from scenario.adapters.x_api import XApiError, search_recent
    calls = []
    def handler(request):
        calls.append(dict(request.url.params))
        assert request.headers["Authorization"] == "Bearer t"
        if "next_token" not in request.url.params:
            return httpx.Response(200, json=X_PAGE)
        return httpx.Response(200, json={**X_PAGE, "meta": {"result_count": 2}})
    pages = search_recent("#x", "t", max_posts=500, transport=httpx.MockTransport(handler))
    assert len(pages) == 2 and calls[1]["next_token"] == "abc" and calls[0]["expansions"].startswith("author_id")
    with pytest.raises(XApiError, match="plan does not include search"):
        search_recent("#x", "t", transport=httpx.MockTransport(lambda r: httpx.Response(403, json={"title": "Forbidden"})))
