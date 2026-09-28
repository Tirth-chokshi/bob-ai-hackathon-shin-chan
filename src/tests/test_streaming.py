import pytest

from engine.schema import Post
from engine.streaming import close, ingest, read_state


def post(post_id, created_at, text="post text"):
    return Post(post_id=post_id, account_id="account-1", username="user", created_at=created_at, text=text)


def test_stream_duplicate_is_idempotent_and_out_of_order_is_retained(tmp_path):
    database = tmp_path / "streams.sqlite"
    duplicate, rows, latest = ingest(database, "stream1", post("p2", 120), 1000)
    assert not duplicate and latest == 120
    duplicate, rows, latest = ingest(database, "stream1", post("p2", 120), 1000)
    assert duplicate and len(rows) == 1

    duplicate, rows, latest = ingest(database, "stream1", post("p1", 90), 1000)
    assert not duplicate and latest == 120
    assert [item.post_id for item in rows] == ["p1", "p2"]

    with pytest.raises(ValueError, match="different post"):
        ingest(database, "stream1", post("p2", 120, "changed content"), 1000)


def test_stream_retention_and_close(tmp_path):
    database = tmp_path / "streams.sqlite"
    ingest(database, "stream1", post("old", 10), 50)
    _, rows, _ = ingest(database, "stream1", post("new", 100), 50)
    assert [item.post_id for item in rows] == ["new"]
    assert close(database, "stream1")
    state, _ = read_state(database, "stream1")
    assert state["status"] == "closed"
    with pytest.raises(ValueError, match="closed"):
        ingest(database, "stream1", post("later", 110), 50)