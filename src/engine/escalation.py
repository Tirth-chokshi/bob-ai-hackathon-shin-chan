from typing import Any
from engine.schema import BobVerdict


def escalate(score: int, verdict: BobVerdict) -> dict[str, Any]:
    """
    Applies deterministic police cyber cell escalation rules based on
    CIB score, threat classification, and offline call-to-action flags.
    """
    threat_type = verdict.threat_type
    severity = verdict.severity
    cta = verdict.offline_call_to_action

    # 1. URGENT rule
    if (threat_type == "incitement" and cta) or (score >= 80 and severity >= 4):
        return {
            "level": "URGENT",
            "actions": [
                "Notify SHO and district control room",
                "Preserve evidence (hashes in brief)",
                "Request platform takedown through the law-enforcement channel (see ITA-69A)",
                "Consider preventive orders (BNSS-163)",
                "Issue a public fact-check advisory"
            ]
        }

    # 2. ALERT rule
    if threat_type in ("organized_misinformation", "targeted_harassment") and score >= 60:
        return {
            "level": "ALERT",
            "actions": [
                "Log lead in cyber cell monitoring register",
                "Preserve evidence and generate verification brief",
                "Monitor campaign hashtag and cluster for amplification",
                "Brief desk officer for potential public clarification"
            ]
        }

    # 3. MONITOR rule
    return {
        "level": "MONITOR",
        "actions": [
            "Routine periodic surveillance",
            "No immediate enforcement action required"
        ]
    }
