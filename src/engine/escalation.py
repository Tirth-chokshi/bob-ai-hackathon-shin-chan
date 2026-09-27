from typing import Any
from engine.schema import BobVerdict


def escalate(score: int, verdict: BobVerdict) -> dict[str, Any]:
    """
    Returns provisional review recommendations. Coordination is not evidence
    of threat intent, and automated output never completes human review.
    """
    threat_type = verdict.threat_type
    severity = verdict.severity
    cta = verdict.offline_call_to_action

    result = {
        "status": "provisional",
        "review_required": True,
        "review_status": verdict.review_status,
        "assessment_status": verdict.assessment_status,
    }

    # A high coordination score is not, by itself, evidence of offline harm.
    if (threat_type == "incitement" and cta and verdict.assessment_status == "classified"
            and len(set(verdict.evidence_post_ids)) >= 2):
        return {
            **result,
            "level": "URGENT",
            "actions": [
                "Priority analyst review of the cited offline-action evidence",
                "Verify the reported action, timing, location, and context",
                "Preserve source records and document review decisions",
                "Consult the appropriate supervisor and legal reviewer before action",
            ],
        }

    # 2. ALERT rule
    if threat_type in ("organized_misinformation", "targeted_harassment") and score >= 60:
        return {
            **result,
            "level": "ALERT",
            "actions": [
                "Analyst review of the evidence and benign explanations",
                "Preserve source records and document verification steps",
                "Assess whether monitoring or a public clarification is appropriate",
            ]
        }

    # 3. MONITOR rule
    return {
        **result,
        "level": "MONITOR",
        "actions": [
            "Routine analyst triage if warranted",
            "Do not infer inauthenticity or intent from coordination alone",
        ]
    }
