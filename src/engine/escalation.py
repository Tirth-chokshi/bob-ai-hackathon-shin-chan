from datetime import tzinfo
from typing import Any
from zoneinfo import ZoneInfo
from engine.schema import BobVerdict
from engine.zones import INDIA, local_text


def escalate(score: int, verdict: BobVerdict, zone: tzinfo = ZoneInfo(INDIA)) -> dict[str, Any]:
    """
    Applies deterministic police cyber cell escalation rules based on
    CIB score, threat classification, and offline call-to-action flags.
    When IBM Bob found a planned gathering, the first actions name its place and time.
    """
    result = _level(score, verdict)
    event = verdict.offline_event
    if event and event.at and result["level"] != "MONITOR":
        deploy_by = local_text(event.at - 3600, zone, "%H:%M on %d %b")
        languages = "Hindi and English" if getattr(zone, "key", "") == INDIA else "the local languages"
        result["actions"] = [
            f"Deploy police at {event.where} before {deploy_by}, an hour before the planned gathering",
            f"Issue a public advisory in {languages} now, before the gathering time",
            *result["actions"],
        ]
    return result


def _level(score: int, verdict: BobVerdict) -> dict[str, Any]:
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
