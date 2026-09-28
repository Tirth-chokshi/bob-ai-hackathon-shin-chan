import pytest
from bob import client
from bob.client import validate_verdict
from bob.legal import load_legal_table
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
    assert verdict.evidence_post_ids == ["p1"]            # post from another campaign dropped
    assert escalate(CAMPAIGN.score, verdict)["level"] == "URGENT"


def test_evidence_limited_to_posts_bob_was_shown():
    shown = [Post(post_id="p2", account_id="a1", username="a1", created_at=0, text="x")]
    verdict = validate_verdict(bob_answer(evidence_post_ids=["p1", "p2"]), CAMPAIGN, load_legal_table(), shown)
    assert verdict.evidence_post_ids == ["p2"]  # p1 is in the campaign but Bob never saw it


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


def test_offline_event_kept_only_when_quoted_and_plausible():
    t0 = 1600750800  # Tue 22 Sep 2020 10:30 IST
    campaign = CAMPAIGN.model_copy(update={"first_seen": t0, "last_seen": t0 + 3600})
    posts = [Post(post_id="p1", account_id="a1", username="u", created_at=t0,
                  text="Aaj shaam 6 baje Rajpura bus stand pe sab log pahuncho")]
    event = {"what": "Crowd called", "where": "Rajpura bus stand", "where_quote": "Rajpura  BUS stand",
             "when": "2020-09-22T18:00:00+05:30"}

    kept = validate_verdict(bob_answer(offline_event=event), campaign, load_legal_table(), posts)
    assert kept.offline_event.at == 1600777800
    actions = escalate(campaign.score, kept)["actions"]
    assert actions[0].startswith("Deploy police at Rajpura bus stand before 17:00 on 22 Sep")

    invented_place = {**event, "where_quote": "Collector office"}
    assert validate_verdict(bob_answer(offline_event=invented_place), campaign, load_legal_table(), posts).offline_event is None
    next_month = {**event, "when": "2020-10-22T18:00:00+05:30"}
    assert validate_verdict(bob_answer(offline_event=next_month), campaign, load_legal_table(), posts).offline_event is None
