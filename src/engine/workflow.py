"""SQLite-backed review state and append-only application audit events."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            dataset_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            status TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT NOT NULL,
            reviewer_id TEXT NOT NULL,
            reviewer_role TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (dataset_id, campaign_id)
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id TEXT NOT NULL,
            campaign_id TEXT,
            actor_id TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            action TEXT NOT NULL,
            previous_status TEXT,
            new_status TEXT,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL,
            details_json TEXT NOT NULL
        )
    """)
    connection.execute("""
        CREATE TRIGGER IF NOT EXISTS audit_events_no_update
        BEFORE UPDATE ON audit_events BEGIN
            SELECT RAISE(ABORT, 'audit events are append-only');
        END
    """)
    connection.execute("""
        CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
        BEFORE DELETE ON audit_events BEGIN
            SELECT RAISE(ABORT, 'audit events are append-only');
        END
    """)
    return connection


def get_review(path: Path, dataset_id: str, campaign_id: str) -> dict:
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT * FROM reviews WHERE dataset_id=? AND campaign_id=?",
            (dataset_id, campaign_id),
        ).fetchone()
    return dict(row) if row else {
        "dataset_id": dataset_id,
        "campaign_id": campaign_id,
        "status": "unreviewed",
        "decision": None,
        "reason": None,
        "reviewer_id": None,
        "reviewer_role": None,
        "updated_at": None,
    }


def record_review(path: Path, dataset_id: str, campaign_id: str, reviewer_id: str,
                  reviewer_role: str, decision: str, reason: str) -> dict:
    if decision in {"downgrade", "reject"} and not reason.strip():
        raise ValueError("A reason is required to downgrade or reject an alert")
    now = datetime.now(timezone.utc).isoformat()
    with _connect(path) as connection:
        current = connection.execute(
            "SELECT status FROM reviews WHERE dataset_id=? AND campaign_id=?",
            (dataset_id, campaign_id),
        ).fetchone()
        previous = current["status"] if current else "unreviewed"
        if previous == "unreviewed" and reviewer_role == "analyst":
            next_status = "analyst_review"
        elif previous == "analyst_review" and reviewer_role == "supervisor":
            next_status = "supervisor_review"
        elif previous == "supervisor_review" and reviewer_role == "supervisor":
            next_status = "closed"
        else:
            raise ValueError(f"Role {reviewer_role} cannot review a campaign in {previous} state")

        with connection:
            connection.execute(
                """INSERT INTO reviews
                   (dataset_id, campaign_id, status, decision, reason, reviewer_id,
                    reviewer_role, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(dataset_id, campaign_id) DO UPDATE SET
                   status=excluded.status, decision=excluded.decision, reason=excluded.reason,
                   reviewer_id=excluded.reviewer_id, reviewer_role=excluded.reviewer_role,
                   updated_at=excluded.updated_at""",
                (dataset_id, campaign_id, next_status, decision, reason.strip(), reviewer_id,
                 reviewer_role, now),
            )
            connection.execute(
                """INSERT INTO audit_events
                   (dataset_id, campaign_id, actor_id, actor_role, action, previous_status,
                    new_status, reason, created_at, details_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (dataset_id, campaign_id, reviewer_id, reviewer_role, decision, previous,
                 next_status, reason.strip(), now, json.dumps({"review_version": 1})),
            )
    return get_review(path, dataset_id, campaign_id)


def list_audit_events(path: Path, dataset_id: str, campaign_id: str | None = None) -> list[dict]:
    query = "SELECT * FROM audit_events WHERE dataset_id=?"
    values: tuple = (dataset_id,)
    if campaign_id:
        query += " AND campaign_id=?"
        values += (campaign_id,)
    query += " ORDER BY id"
    with _connect(path) as connection:
        rows = connection.execute(query, values).fetchall()
    return [dict(row) for row in rows]