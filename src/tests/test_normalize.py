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
    assert p.source_name == f.name and p.source_id == tmp_path.name
    assert p.source_row == 1 and len(p.original_record_sha256) == 64
    assert len(p.normalized_record_sha256) == 64
    assert p.field_origins["username"] == "supplied"
    assert p.field_origins["urls"] == "defaulted"


def test_text_only_dataset_explains_why(tmp_path):
    f = tmp_path / "constraint.csv"
    f.write_text("Unique ID,Post,Labels Set\n1,some text,fake\n", encoding="utf-8")
    with pytest.raises(ValueError, match="who posted it.*when it was posted.*text-only"):
        load_posts(f)
