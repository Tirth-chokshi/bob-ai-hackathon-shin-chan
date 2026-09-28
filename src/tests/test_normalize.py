import json
import pytest
from engine.normalize import load_posts

# An export with other column names, semicolons and an Excel byte-order mark
MESSY_CSV = """﻿Tweet ID;User;Timestamp;Content;In Reply To
1;@asha;2026-09-23T14:05:12Z;Gather at the Collector office 7 PM! #SundarpurAlert http://x.example/a;
2;ravi;1790172312000;same text again;1
3;meena;Wed Sep 23 14:05:30 +0000 2026;no tags here;
4;;2026-09-23 14:06:00;no account, skipped;
"""


def test_messy_csv(tmp_path):
    f = tmp_path / "export.csv"
    f.write_text(MESSY_CSV, encoding="utf-8")
    posts = load_posts(f)
    assert [p.post_id for p in posts] == ["1", "2", "3"]           # row without an account skipped
    assert posts[0].account_id == "@asha" and posts[0].created_at == 1790172312
    assert posts[0].hashtags == ["#SundarpurAlert"]                  # taken from the text
    assert posts[0].urls == ["http://x.example/a"]
    assert posts[1].created_at == 1790172312 and posts[1].reply_to == "1"  # epoch milliseconds
    assert posts[2].created_at == 1790172330                          # Twitter date format


def test_json_upload(tmp_path):
    f = tmp_path / "posts.json"
    f.write_text(json.dumps([{"id": "a", "author": "x", "date": "2026-09-23", "message": "hi"}]), encoding="utf-8")
    [p] = load_posts(f)
    assert (p.post_id, p.account_id, p.text) == ("a", "x", "hi")


def test_text_only_dataset_explains_why(tmp_path):
    f = tmp_path / "constraint.csv"
    f.write_text("Unique ID,Post,Labels Set\n1,some text,fake\n", encoding="utf-8")
    with pytest.raises(ValueError, match="who posted it.*when it was posted.*text-only"):
        load_posts(f)


def test_new_columns_and_language():
    from engine.normalize import load_rows
    rows = [{"user": "a", "time": "2020-09-22 10:00", "text": "आज शाम 6 बजे", "source": "WhatsApp", "location": "Rajpura"},
            {"user": "b", "time": "2020-09-22 10:01", "text": "aaj shaam sab log pahuncho"}]
    posts = load_rows(rows, ["user", "time", "text", "source", "location"])
    assert (posts[0].platform, posts[0].city) == ("whatsapp", "Rajpura")


def test_whatsapp_export(tmp_path):
    f = tmp_path / "chat.txt"
    f.write_text(
        "22/09/20, 09:59 - Messages and calls are end-to-end encrypted.\n"
        "22/09/20, 10:02 - Ramesh Ji: सावधान! राजपुरा बस स्टैंड https://youtu.be/k7\n"
        "sab group mein bhejo\n"
        "22/09/20, 6:05 pm - +91 98XXX X4521: <Media omitted>\n"
        "[22/09/20, 10:03:15] Pintu: aaj shaam 6 baje sab log pahuncho\n",
        encoding="utf-8")
    posts = load_posts(f)
    assert [p.username for p in posts] == ["Ramesh Ji", "+91 98XXX X4521", "Pintu"]  # system line skipped
    assert posts[0].text.endswith("sab group mein bhejo")                          # multi-line message
    assert posts[0].created_at == 1600749120                                        # 10:02 IST
    assert posts[1].created_at == 1600778100                                        # 6:05 pm IST
    assert posts[0].urls == ["https://youtu.be/k7"] and posts[0].platform == "whatsapp"
    assert [p.language for p in posts] == ["hi", None, "hinglish"]  # "<Media omitted>" has no language


def test_telegram_export(tmp_path):
    f = tmp_path / "result.json"
    f.write_text(json.dumps({"name": "PSSB Updates", "id": 77, "messages": [
        {"id": 1, "type": "service", "date": "2020-09-26T20:00:00", "action": "create_channel"},
        {"id": 2, "type": "message", "date": "2020-09-26T20:02:00", "date_unixtime": "1601130720",
         "from": "PSSB Updates", "from_id": "channel77", "text": ["Paper leak! join ", {"type": "link", "text": "https://t.me/x"}]},
        {"id": 3, "type": "message", "date": "2020-09-26T20:05:00", "from": "Ravi", "from_id": "user5",
         "text": "fake hai", "reply_to_message_id": 2},
    ]}), encoding="utf-8")
    posts = load_posts(f)
    assert [p.post_id for p in posts] == ["tg_77_2", "tg_77_3"]
    assert posts[0].text == "Paper leak! join https://t.me/x" and posts[0].urls == ["https://t.me/x"]
    assert posts[1].reply_to == "tg_77_2" and posts[1].created_at == 1601130900  # 20:05 IST
    assert posts[0].account_id == "tg:channel77" and posts[0].platform == "telegram"
