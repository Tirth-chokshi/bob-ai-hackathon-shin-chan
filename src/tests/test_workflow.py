import sqlite3

import pytest

from engine.workflow import get_review, list_audit_events, record_review


def test_review_requires_analyst_then_supervisor_and_appends_audit(tmp_path):
    database = tmp_path / "workflow.sqlite"
    assert get_review(database, "run1", "c1")["status"] == "unreviewed"

    with pytest.raises(ValueError, match="cannot review"):
        record_review(database, "run1", "c1", "supervisor-1", "supervisor", "accept", "")

    first = record_review(database, "run1", "c1", "analyst-1", "analyst", "downgrade", "Benign event")
    assert first["status"] == "analyst_review"
    second = record_review(database, "run1", "c1", "supervisor-1", "supervisor", "accept", "Verified context")
    assert second["status"] == "supervisor_review"
    final = record_review(database, "run1", "c1", "supervisor-1", "supervisor", "accept", "Closed")
    assert final["status"] == "closed"

    events = list_audit_events(database, "run1", "c1")
    assert len(events) == 3
    assert events[0]["previous_status"] == "unreviewed"
    assert events[-1]["new_status"] == "closed"
    with sqlite3.connect(database) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM audit_events")


def test_downgrade_and_rejection_require_reason(tmp_path):
    with pytest.raises(ValueError, match="reason is required"):
        record_review(tmp_path / "workflow.sqlite", "run1", "c1", "a", "analyst", "reject", " ")