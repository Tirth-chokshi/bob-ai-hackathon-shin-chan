"""The only input format (X API v2 JSON) and the database it is stored in (engine/xstore.py, docs/data-model.md)."""
import json

import pytest

from engine.normalize import detect_language
from engine.xstore import NotXApiData, build, check, ingest, load_posts, read_file, read_posts
from tests.fixtures import X_PAGE, iso, x_post


def test_x_page_mapped_onto_posts(tmp_path):
    f = tmp_path / "search.json"
    f.write_text(json.dumps(X_PAGE, ensure_ascii=False), encoding="utf-8")
    posts, warnings = ingest(f, tmp_path / "x.db")
    a, b, c = posts
    assert (a.post_id, a.account_id, a.username, a.display_name, a.platform, a.repost_of, a.city) == \
        ("1308", "u1", "alert_rahul", "Rahul", "x", "1300", "Rajpura")
    assert a.text == "RT @orig: राजपुरा बस स्टैंड के पास बच्चा चोर गिरोह घूम रहा है, पूरा संदेश"  # original from includes, in full
    assert a.hashtags == ["#बच्चा_चोर"] and a.urls == ["https://youtu.be/k7"] and a.account_created_at == 1600509600
    assert (a.followers, a.verified, a.metrics["reposts"], a.conversation_id) == (12, False, 41, "1300")
    assert b.text == "@NavgarhPolice the full long text" and b.reply_to == "1301" and b.city == "Navgarh, India"
    assert b.reply_to_user == "NavgarhPolice" and b.verified is True and b.language == "en"  # "und" -> detected
    assert (c.quote_of, c.media, c.metrics) == ("1300", ["photo"], {"likes": 17, "reposts": 2, "replies": 5,
                                                                   "quotes": 1, "views": 940})
    assert warnings == []


def test_database_tables_follow_the_x_data_dictionary(tmp_path):
    db = build([X_PAGE], tmp_path / "x.db")
    cols = lambda t: [r[1] for r in db.execute(f"PRAGMA table_info({t})")]
    assert {"id", "text", "author_id", "created_at", "conversation_id", "in_reply_to_user_id", "lang",
            "retweet_count", "reply_count", "like_count", "quote_count", "impression_count"} <= set(cols("tweets"))
    assert {"id", "username", "name", "created_at", "location", "verified", "followers_count"} <= set(cols("users"))
    assert cols("referenced_tweets") == ["tweet_id", "type", "id"]
    # the referenced original is stored for context, not analysed
    assert db.execute("SELECT source FROM tweets WHERE id = '1300'").fetchone() == ("includes",)
    assert [p.post_id for p in read_posts(db)] == ["1308", "1309", "1310"]
    assert [p.post_id for p in read_posts(db, source="includes")] == ["1300"]


@pytest.mark.parametrize("data, reason", [
    ([{"post_id": "p1", "account_id": "a", "created_at": "2021-01-26", "text": "x"}], 'no "data"'),       # our old flat rows
    ({"id_str": "9", "user": {"screen_name": "a"}, "full_text": "x"}, "v1.1"),                              # v1.1 tweet
    ({"data": [{"id": "1", "text": "x", "author_id": "a"}]}, "without created_at"),                          # field not requested
    ({"data": [{"id": "1", "text": "x", "author_id": "a", "created_at": "26/01/2021"}]}, "ISO 8601"),
    ({"data": [], "meta": {"result_count": 0}}, "no posts"),
])
def test_anything_else_is_refused_with_the_reason(data, reason):
    responses = data if isinstance(data, list) else [data]
    with pytest.raises(NotXApiData, match=reason):
        check(responses)


def test_warns_when_recommended_fields_are_missing():
    warnings = check([{"data": [{"id": "1", "text": "x", "author_id": "a", "created_at": iso(0)}]}])
    assert any("includes.users" in w for w in warnings) and any("public_metrics" in w for w in warnings)


def test_pages_and_stream_lines_with_overlap_store_each_post_once(tmp_path):
    line = lambda i: json.dumps({"data": x_post(str(i), "u1", 1000 + i, f"post {i}"), "matching_rules": [{"id": "r1", "tag": "rumour"}],
                                 "includes": {"users": [{"id": "u1", "username": "alert_rahul"}]}})
    f = tmp_path / "stream.jsonl"
    f.write_text("\n".join([line(1), line(2), line(2)]), encoding="utf-8")
    assert len(read_file(f)) == 3
    assert [p.post_id for p in load_posts(f)] == ["1", "2"]
    db = build(read_file(f), tmp_path / "x.db")
    assert db.execute("SELECT COUNT(*) FROM matching_rules WHERE tag = 'rumour'").fetchone()[0] >= 2


def test_language_detection_for_posts_x_marks_und():
    assert detect_language("राजपुरा बस स्टैंड के पास") == "hi"
    assert detect_language("Rajpura bus stand ke paas gang active hai") == "hinglish"
    assert detect_language("Место крушения самолета") == "ru"
    assert detect_language("https://t.co/abc") is None


def test_x_recent_search_follows_next_token():
    import httpx
    from connectors.x_search import XApiError, search_recent
    calls = []

    def handler(request):
        calls.append(dict(request.url.params))
        assert request.headers["Authorization"] == "Bearer t"
        if "next_token" not in request.url.params:
            return httpx.Response(200, json=X_PAGE)
        return httpx.Response(200, json={**X_PAGE, "meta": {"result_count": 3}})

    pages = search_recent("#x", "t", max_posts=500, transport=httpx.MockTransport(handler))
    assert len(pages) == 2 and calls[1]["next_token"] == "abc" and "public_metrics" in calls[0]["tweet.fields"]
    with pytest.raises(XApiError, match="plan does not include search"):
        search_recent("#x", "t", transport=httpx.MockTransport(lambda r: httpx.Response(403, json={"title": "Forbidden"})))
