import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo
from config import BOB_API_KEY, BOB_MAX_COST, BOB_RULES
from engine.schema import Campaign, Post, BobVerdict
from engine.scoring import WEIGHTS
from engine.normalize import parse_time
from engine.zones import INDIA, dataset_zone, local_text
from bob.legal import load_legal_table, allowed_offence_ids

log = logging.getLogger(__name__)


class BobNotConfigured(Exception):
    pass


def is_bob_configured() -> bool:
    return bool(BOB_API_KEY and get_bob_cmd())


def get_bob_cmd() -> list[str] | None:
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        bob_js = Path(appdata) / "npm/node_modules/bobshell/dist/bob.js"
        if bob_js.exists():
            return ["node", str(bob_js)]
    bob_bin = shutil.which("bob")
    if bob_bin:
        return [bob_bin]
    for p in [
        Path.home() / ".npm-global/bin/bob",
        Path.home() / ".local/bin/bob",
        Path("/usr/local/bin/bob"),
        Path("/usr/bin/bob"),
    ]:
        if p.is_file() and os.access(p, os.X_OK):
            return [str(p)]
    return None


def run_bob(
    prompt: str,
    work_dir: Path | str,
    instruction: str = "Classify the campaign described on stdin. Follow its instructions exactly.",
    max_cost: str = BOB_MAX_COST,
) -> tuple[str, float]:
    """Runs a headless Bob inference call via CLI with JSON output format. The prompt goes via stdin."""
    bob_cmd = get_bob_cmd()
    if not bob_cmd:
        raise FileNotFoundError("[Errno 2] No such file or directory: 'bob'")
    cmd = [
        *bob_cmd,
        "run",
        "--accept-license",
        "--format",
        "json",
        "--max-turns",
        "2",
        "--max-cost",
        str(max_cost),
        "--disable-mcp",
        "--disable-subagents",
        instruction,
    ]

    env = {**os.environ}
    if BOB_API_KEY:
        env["BOB_API_KEY"] = BOB_API_KEY

    res = subprocess.run(
        cmd,
        input=prompt,
        cwd=str(work_dir),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120
    )

    if res.returncode != 0:
        raise RuntimeError(f"Bob execution failed (exit code {res.returncode}): {res.stderr}")

    # One JSON object, or one event per line (e.g. an error event before the result)
    try:
        events = [json.loads(res.stdout)]
    except json.JSONDecodeError:
        events = [json.loads(line) for line in res.stdout.splitlines() if line.strip()]
    errors = [e.get("message", "") for e in events if e.get("type") == "error"]
    result = next((e for e in reversed(events) if "last_message" in e), None)
    if errors or not result:
        raise RuntimeError(f"Bob run failed: {'; '.join(errors) or res.stdout[:500]}")
    return result["last_message"], float(result.get("stats", {}).get("session_costs", 0.0))


def extract_json(text: str) -> dict:
    text = text.strip()
    # Check for markdown code blocks
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    else:
        # Find first { to last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]
    return json.loads(text)


def build_classification_prompt(
    campaign: Campaign,
    sample_posts: list[Post],
    allowed_ids: list[str],
    zone: tzinfo = ZoneInfo(INDIA),
) -> str:
    rules_text = ""
    for r_file in sorted(BOB_RULES.glob("*.md")):
        rules_text += f"\n--- {r_file.name} ---\n{r_file.read_text(encoding='utf-8')}\n"

    posts_repr = [
        {
            "post_id": p.post_id,
            "posted_at": local_text(p.created_at, zone),
            "platform": p.platform,
            "town": p.city,
            "username": p.username,
            "text": p.text,
            "urls": p.urls,
            "repost_of": p.repost_of,
            "reply_to": p.reply_to,
            "account_created": local_text(p.account_created_at, zone, "%d %b %Y"),
        }
        for p in sample_posts
    ]
    score_breakdown = {
        name: {
            "points": points,
            "max_points": int(100 * WEIGHTS[name]),
            "weight": WEIGHTS[name],
        }
        for name, points in campaign.features.items()
        if name in WEIGHTS
    }
    campaign_analysis = {
        "campaign_id": campaign.id,
        "coordination_score": campaign.score,
        "score_components": score_breakdown,
        "account_count": campaign.size,
        "post_count": len(campaign.post_ids),
        "top_hashtag": campaign.top_hashtag,
        "coordination_signals": campaign.signals,
        "first_seen": local_text(campaign.first_seen, zone),
        "last_seen": local_text(campaign.last_seen, zone),
        "median_account_age_days": campaign.median_account_age_days,
        "platforms_in_order_reached": [f"{x['name']} ({local_text(x['first_seen'], zone)})" for x in campaign.platform_path],
        "towns_in_order_reached": [f"{x['name']} ({local_text(x['first_seen'], zone)})" for x in campaign.town_path],
        "languages": campaign.languages,
    }

    zone_name = getattr(zone, "key", str(zone))
    utc_offset = datetime.fromtimestamp(campaign.first_seen, zone).strftime("%z")
    utc_offset = f"{utc_offset[:3]}:{utc_offset[3:]}"
    prompt = f"""You are a police cyber cell threat analyst in India evaluating a coordinated social media campaign.
The campaign may come from any country and be in any language: describe what it is about and whom it targets
on its own terms, and do not comment on whether it concerns India.

RULES & LEGAL CONTEXT:
{rules_text}

CAMPAIGN ANALYSIS (times are local time, {zone_name}; score components show points, maximum points, and weight):
{json.dumps(campaign_analysis, indent=2, ensure_ascii=False)}

REPRESENTATIVE POSTS (sampled across the whole campaign; they may be in any language, e.g. Hindi or Hinglish):
{json.dumps(posts_repr, indent=2, ensure_ascii=False)}

ALLOWED LEGAL OFFENCE IDs (choose ONLY from this list):
{', '.join(allowed_ids)}

OUTPUT INSTRUCTIONS:
Analyze the behaviour and text. Reply with ONLY a single valid JSON object adhering to this schema:
{{
  "threat_type": "one of: incitement, targeted_harassment, organized_misinformation, benign_coordination",
  "target": "target description",
  "narrative": "short summary of the campaign narrative",
  "severity": <integer 1 to 5>,
  "offline_call_to_action": <boolean>,
  "legal_suggestions": [
    {{"id": "<allowed_id>", "why": "<one line explanation>"}}
  ],
  "evidence_post_ids": ["<post_ids from sample posts>"],
  "offline_event": null or {{
    "what": "<what people are called to do offline, in English>",
    "where": "<the place, in English>",
    "where_quote": "<the place copied exactly as written in one of the posts, same script>",
    "when": "<ISO 8601 date-time with the UTC offset {utc_offset}, resolving words like 'aaj shaam 6 baje' from the post's time>"
  }}
}}
Write target and narrative in English whatever the language of the posts.
Set offline_event only if posts call people to a specific place at a specific time; otherwise null.
Do NOT output any markdown wrappers, conversational greetings, or notes. ONLY JSON."""
    return prompt


def cached_verdict(run_dir: Path, campaign_id: str) -> BobVerdict | None:
    path = Path(run_dir) / "bob" / f"{campaign_id}.json"
    return BobVerdict.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None


def validate_verdict(data: dict, campaign: Campaign, legal_table: dict, posts: list[Post] = ()) -> BobVerdict:
    """Schema-check Bob's answer, keep only offence IDs from our legal table and post IDs from this campaign,
    and keep the offline event only if its place is quoted from a post and its time is plausible."""
    verdict = BobVerdict.model_validate(data)
    verdict.legal_suggestions = [
        s.model_copy(update={k: legal_table[s.id][k] for k in ("title", "law", "ipc")})
        for s in verdict.legal_suggestions
        if legal_table.get(s.id, {}).get("kind") == "offence"
    ]
    allowed = set(campaign.post_ids)
    if posts:  # Bob can only cite the posts it was shown
        allowed &= {p.post_id for p in posts}
    verdict.evidence_post_ids = [pid for pid in verdict.evidence_post_ids if pid in allowed]
    if not verdict.evidence_post_ids:
        raise ValueError("no evidence post IDs from the posts Bob was shown")

    event = verdict.offline_event
    if event:
        squash = lambda s: " ".join(s.lower().split())
        quoted = squash(event.where_quote) and any(squash(event.where_quote) in squash(p.text) for p in posts)
        at = parse_time(event.when)
        plausible = at is not None and campaign.first_seen - 86400 <= at <= campaign.last_seen + 3 * 86400
        verdict.offline_event = event.model_copy(update={"at": at}) if quoted and plausible else None
        if not verdict.offline_event:
            log.info("Dropped Bob's offline event for %s (place not quoted from a post or implausible time)", campaign.id)
    return verdict


def classify(
    run_dir: Path,
    campaign: Campaign,
    sample_posts: list[Post]
) -> tuple[BobVerdict, float, bool]:
    """
    Classifies a coordinated campaign using IBM Bob with schema validation,
    legal table filtering, and disk caching.
    Returns (verdict, cost, is_cached).
    """
    run_dir = Path(run_dir)
    verdict = cached_verdict(run_dir, campaign.id)
    if verdict:
        return verdict, 0.0, True

    if not BOB_API_KEY:
        raise BobNotConfigured("BOB_API_KEY is missing from src/.env.")
    bob_cmd = get_bob_cmd()
    if not bob_cmd:
        raise BobNotConfigured("IBM Bob Shell CLI was not found. Install Bob Shell and ensure `bob` is on the backend PATH.")

    legal_table = load_legal_table()
    prompt = build_classification_prompt(campaign, sample_posts, allowed_offence_ids(), dataset_zone(run_dir))

    cost = 0.0
    verdict = None
    last_error = None
    with tempfile.TemporaryDirectory() as tmp_dir:
        for _ in range(2):
            try:
                raw_resp, call_cost = run_bob(prompt, work_dir=tmp_dir)
                cost += call_cost
                verdict = validate_verdict(extract_json(raw_resp), campaign, legal_table, sample_posts)
                break
            except Exception as e:
                last_error = e
                log.warning("Live Bob CLI inference attempt failed: %s", e)

    if verdict is None:
        raise RuntimeError(f"IBM Bob failed to return a valid assessment: {last_error}") from last_error

    bob_dir = run_dir / "bob"
    bob_dir.mkdir(parents=True, exist_ok=True)
    (bob_dir / f"{campaign.id}.json").write_text(verdict.model_dump_json(indent=2), encoding="utf-8")
    # the brief summary was written from the old verdicts
    (bob_dir / "summary.json").unlink(missing_ok=True)
    return verdict, cost, False
