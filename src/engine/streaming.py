"""SQLite event-time storage for bounded rolling-window analysis streams."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from engine.schema import Post


def _comparison_payload(post: Post) -> str:
    data = post.model_dump(exclude={"ingested_at", "source_row", "normalized_record_sha256"})
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS stream_state (
            stream_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'active',
            latest_event_time INTEGER,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            alert_json TEXT NOT NULL DEFAULT '{}'
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS stream_posts (
            stream_id TEXT NOT NULL,
            post_id TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (stream_id, post_id)
        )
    """)
    connection.execute("CREATE INDEX IF NOT EXISTS stream_posts_time ON stream_posts(stream_id, created_at)")
    return connection


def ingest(path: Path, stream_id: str, post: Post, retention_seconds: int) -> tuple[bool, list[Post], int]:
    """Persist a post once and return active-window posts and event-time watermark."""
    payload = post.model_dump_json()
    with closing(_connect(path)) as connection:
        state = connection.execute("SELECT status FROM stream_state WHERE stream_id=?", (stream_id,)).fetchone()
        existing = connection.execute(
            "SELECT payload_json FROM stream_posts WHERE stream_id=? AND post_id=?",
            (stream_id, post.post_id),
        ).fetchone()
        if existing:
            if _comparison_payload(Post.model_validate_json(existing["payload_json"])) != _comparison_payload(post):
                raise ValueError("A different post with this post_id already exists in the stream")
            latest = connection.execute(
                "SELECT MAX(created_at) AS latest FROM stream_posts WHERE stream_id=?", (stream_id,)
            ).fetchone()["latest"]
            duplicate = True
        else:
            if state and state["status"] == "closed":
                raise ValueError("This stream is closed")
            with connection:
                connection.execute("INSERT INTO stream_state(stream_id) VALUES (?) ON CONFLICT DO NOTHING", (stream_id,))
                connection.execute(
                    "INSERT INTO stream_posts(stream_id, post_id, created_at, payload_json) VALUES (?, ?, ?, ?)",
                    (stream_id, post.post_id, post.created_at, payload),
                )
                latest = max(post.created_at, connection.execute(
                    "SELECT latest_event_time FROM stream_state WHERE stream_id=?", (stream_id,)
                ).fetchone()[0] or post.created_at)
                connection.execute(
                    "UPDATE stream_state SET latest_event_time=?, updated_at=CURRENT_TIMESTAMP WHERE stream_id=?",
                    (latest, stream_id),
                )
                connection.execute(
                    "DELETE FROM stream_posts WHERE stream_id=? AND created_at<?",
                    (stream_id, latest - max(1, retention_seconds)),
                )
            duplicate = False

        rows = connection.execute(
            "SELECT payload_json FROM stream_posts WHERE stream_id=? ORDER BY created_at, post_id",
            (stream_id,),
        ).fetchall()
    retained = [Post.model_validate_json(row["payload_json"]) for row in rows]
    return duplicate, retained, int(latest)


def save_alert(path: Path, stream_id: str, alert: dict) -> None:
    with closing(_connect(path)) as connection, connection:
        connection.execute(
            "UPDATE stream_state SET alert_json=?, updated_at=CURRENT_TIMESTAMP WHERE stream_id=?",
            (json.dumps(alert), stream_id),
        )


def read_state(path: Path, stream_id: str) -> tuple[dict, list[Post]] | None:
    with closing(_connect(path)) as connection:
        state = connection.execute("SELECT * FROM stream_state WHERE stream_id=?", (stream_id,)).fetchone()
        if not state:
            return None
        rows = connection.execute(
            "SELECT payload_json FROM stream_posts WHERE stream_id=? ORDER BY created_at, post_id",
            (stream_id,),
        ).fetchall()
    return ({**dict(state), "alert": json.loads(state["alert_json"])},
            [Post.model_validate_json(row["payload_json"]) for row in rows])


def close(path: Path, stream_id: str) -> bool:
    with closing(_connect(path)) as connection:
        with connection:
            cursor = connection.execute(
                "UPDATE stream_state SET status='closed', updated_at=CURRENT_TIMESTAMP WHERE stream_id=? AND status='active'",
                (stream_id,),
            )
    return cursor.rowcount == 1