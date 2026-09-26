import pytest
from bob.client import validate_verdict
from bob.legal import load_legal_table
from engine.escalation import escalate
from engine.schema import Campaign

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


@pytest.mark.parametrize("bad", [
    {"threat_type": "terrorism"},          # not one of our labels
    {"severity": 7},                       # outside 1-5
    {"evidence_post_ids": ["p999"]},       # no evidence from this campaign
])
def test_rejects_invalid_answers(bad):
    with pytest.raises(ValueError):
        validate_verdict(bob_answer(**bad), CAMPAIGN, load_legal_table())
