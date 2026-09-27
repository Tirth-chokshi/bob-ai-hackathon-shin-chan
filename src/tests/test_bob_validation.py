import pytest
import json
from bob import client
from bob.client import validate_verdict
from bob.legal import LEGAL_METADATA_PATH, load_legal_metadata, load_legal_table
from engine.escalation import escalate
from engine.schema import Campaign, Post

CAMPAIGN = Campaign(
    id="c1", accounts=["a1", "a2"], post_ids=["p1", "p2", "p3"], size=2, score=85,
    features={}, signals=["co_tweet"], first_seen=0, last_seen=60,
)


def bob_answer(**overrides):
    answer = {
        "threat_type": "incitement",
        "target": "residents",
        "narrative": "dam rumour with a 7 PM gathering call",
        "severity": 4,
        "offline_call_to_action": True,
        "legal_suggestions": [
            {"id": "BNS-353", "why": "rumour causing alarm"},
            {"id": "ITA-66A", "why": "struck down, must be dropped"},
            {"id": "BNSS-163", "why": "procedural, not an offence"},
        ],
        "evidence_post_ids": ["p1", "p999"],
    }
    return {**answer, **overrides}


def test_whitelists_legal_ids_and_evidence():
    verdict = validate_verdict(bob_answer(), CAMPAIGN, load_legal_table())
    assert [s.id for s in verdict.legal_suggestions] == ["BNS-353"]
    assert verdict.legal_suggestions[0].law == "BNS 353"  # enriched from the table
    assert verdict.legal_suggestions[0].reference_version == "unreviewed-2026-09-27"
    assert verdict.legal_suggestions[0].review_status == "pending_qualified_review"
    assert verdict.evidence_post_ids == ["p1"]            # post from another campaign dropped
    result = escalate(CAMPAIGN.score, verdict)
    assert result["level"] == "MONITOR"  # one cited post is insufficient for urgent escalation
    assert result["status"] == "provisional" and result["review_required"]


def test_validates_structured_offline_indicators_and_evidence_scope():
    indicator = {
        "kind": "event_time",
        "value": "2026-09-27T19:00:00+05:30",
        "evidence_post_ids": ["p1", "p999"],
        "verification_required": True,
    }
    verdict = validate_verdict(bob_answer(offline_indicators=[indicator]), CAMPAIGN,
                               load_legal_table(), {"p1", "p2"})
    assert verdict.offline_indicators[0].evidence_post_ids == ["p1"]
    assert verdict.offline_indicators[0].verification_required is True

    with pytest.raises(ValueError, match="no evidence"):
        validate_verdict(bob_answer(offline_indicators=[{**indicator, "evidence_post_ids": ["p999"]}]),
                         CAMPAIGN, load_legal_table(), {"p1", "p2"})


def test_rejects_malformed_or_timezone_free_offline_times():
    with pytest.raises(ValueError, match="ISO-8601"):
        validate_verdict(bob_answer(offline_indicators=[{
            "kind": "event_time", "value": "tomorrow at 7", "evidence_post_ids": ["p1"]
        }]), CAMPAIGN, load_legal_table())
    with pytest.raises(ValueError, match="timezone"):
        validate_verdict(bob_answer(offline_indicators=[{
            "kind": "event_time", "value": "2026-09-27T19:00:00", "evidence_post_ids": ["p1"]
        }]), CAMPAIGN, load_legal_table())


def test_high_coordination_score_alone_never_produces_urgent():
    verdict = validate_verdict(bob_answer(
        threat_type="benign_coordination",
        offline_call_to_action=False,
        evidence_post_ids=["p1", "p2"],
    ), CAMPAIGN, load_legal_table())
    assert escalate(CAMPAIGN.score, verdict)["level"] == "MONITOR"


def test_urgent_requires_multiple_valid_offline_action_evidence_posts():
    verdict = validate_verdict(bob_answer(evidence_post_ids=["p1", "p2"]), CAMPAIGN, load_legal_table())
    result = escalate(CAMPAIGN.score, verdict)
    assert result["level"] == "URGENT"
    assert result["review_required"] is True


@pytest.mark.parametrize("bad", [
    {"threat_type": "terrorism"},          # not one of our labels
    {"severity": 7},                       # outside 1-5
    {"evidence_post_ids": ["p999"]},       # no evidence from this campaign
])
def test_rejects_invalid_answers(bad):
    with pytest.raises(ValueError):
        validate_verdict(bob_answer(**bad), CAMPAIGN, load_legal_table())


def test_prompt_includes_campaign_analysis_and_all_samples():
    campaign = CAMPAIGN.model_copy(update={
        "features": {"speed": 20, "duplication": 21, "multi_signal": 12},
        "top_hashtag": "#example",
        "median_account_age_days": 14,
    })
    posts = [
        Post(post_id=f"p{index}", account_id="a1", username="user", created_at=index,
             text=f"post {index}")
        for index in range(20)
    ]

    prompt = client.build_classification_prompt(campaign, posts, [])

    assert '"coordination_score": 85' in prompt
    assert '"median_account_age_days": 14' in prompt
    assert '"max_points": 25' in prompt
    assert '"post_id": "p19"' in prompt


def test_prompt_discloses_legal_reference_review_status():
    table = load_legal_table()
    prompt = client.build_classification_prompt(CAMPAIGN, [], [], next(iter(table.values())))
    assert "unreviewed-2026-09-27" in prompt
    assert "pending_qualified_review" in prompt
    assert "never charges or legal conclusions" in prompt


def test_rejects_legal_metadata_kind_drift(tmp_path):
    table = load_legal_table()
    metadata = json.loads(LEGAL_METADATA_PATH.read_text(encoding="utf-8"))
    metadata["provisions"][0]["kind"] = "procedural"
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="kind mismatch"):
        load_legal_metadata(table, path)


def test_classify_requires_bob_cli_instead_of_returning_heuristic(tmp_path, monkeypatch):
    monkeypatch.setattr(client, "BOB_API_KEY", "test-key")
    monkeypatch.setattr(client, "get_bob_cmd", lambda: None)

    with pytest.raises(client.BobNotConfigured, match="CLI was not found"):
        client.classify(tmp_path, CAMPAIGN, [])

    assert not (tmp_path / "bob" / "c1.json").exists()


def test_classify_does_not_fall_back_when_bob_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(client, "BOB_API_KEY", "test-key")
    monkeypatch.setattr(client, "get_bob_cmd", lambda: ["bob"])
    calls = 0

    def fail_bob(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise RuntimeError("Bob unavailable")

    monkeypatch.setattr(client, "run_bob", fail_bob)
    with pytest.raises(RuntimeError, match="IBM Bob failed"):
        client.classify(tmp_path, CAMPAIGN, [])

    assert calls == 2
    assert not (tmp_path / "bob" / "c1.json").exists()
