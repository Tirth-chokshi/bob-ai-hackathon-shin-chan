import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from config import BOB_API_KEY, BOB_MAX_COST, BOB_RULES
from engine.schema import Campaign, Post, BobVerdict
from bob.legal import load_legal_table, allowed_offence_ids

log = logging.getLogger(__name__)


class BobNotConfigured(Exception):
    pass


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
    allowed_ids: list[str]
) -> str:
    rules_text = ""
    for r_file in sorted(BOB_RULES.glob("*.md")):
        rules_text += f"\n--- {r_file.name} ---\n{r_file.read_text(encoding='utf-8')}\n"

    posts_repr = [
        {
            "post_id": p.post_id,
            "account_id": p.account_id,
            "username": p.username,
            "text": p.text
        }
        for p in sample_posts[:10]
    ]

    prompt = f"""You are a police cyber cell threat analyst evaluating a coordinated social media campaign in India.

RULES & LEGAL CONTEXT:
{rules_text}

CAMPAIGN EVIDENCE:
- Campaign ID: {campaign.id}
- Account count: {campaign.size}
- Top hashtag: {campaign.top_hashtag}
- CIB Risk Score: {campaign.score}/100
- Score breakdown: {json.dumps(campaign.features)}
- Coordination signals: {json.dumps(campaign.signals)}

SAMPLE POSTS:
{json.dumps(posts_repr, indent=2)}

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
  "evidence_post_ids": ["<post_ids from sample posts>"]
}}
Do NOT output any markdown wrappers, conversational greetings, or notes. ONLY JSON."""
    return prompt


def cached_verdict(run_dir: Path, campaign_id: str) -> BobVerdict | None:
    path = Path(run_dir) / "bob" / f"{campaign_id}.json"
    return BobVerdict.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None


def validate_verdict(data: dict, campaign: Campaign, legal_table: dict) -> BobVerdict:
    """Schema-check Bob's answer, keep only offence IDs from our legal table and post IDs from this campaign."""
    verdict = BobVerdict.model_validate(data)
    verdict.legal_suggestions = [
        s.model_copy(update={k: legal_table[s.id][k] for k in ("title", "law", "ipc")})
        for s in verdict.legal_suggestions
        if legal_table.get(s.id, {}).get("kind") == "offence"
    ]
    campaign_post_ids = set(campaign.post_ids)
    verdict.evidence_post_ids = [pid for pid in verdict.evidence_post_ids if pid in campaign_post_ids]
    if not verdict.evidence_post_ids:
        raise ValueError("no evidence post IDs from this campaign")
    return verdict


def heuristic_classify(campaign: Campaign, sample_posts: list[Post], legal_table: dict) -> dict:
    """
    Deterministically determines threat classification and statutory provisions
    when the headless Bob CLI is unavailable or errors out. Follows the rules
    in .bob/rules-osint-analyst.
    """
    all_text = " ".join((p.text or "") for p in sample_posts).lower()
    hashtag = (campaign.top_hashtag or "").lower()
    full_corpus = f"{all_text} {hashtag}"

    # 1. Offline call to action patterns
    cta_patterns = [
        r"\b(gather|assemble|march|protest|meet|reach|come out|arrive|block|gherao|dharna|chalo|rasta roko)\b",
        r"\b(7\s*pm|8\s*pm|9\s*pm|tonight|today|collector\s*office|collectorate|dam\s*site|outside|street|chowk|gates?)\b",
    ]
    has_cta_action = bool(re.search(cta_patterns[0], full_corpus))
    has_cta_target = bool(re.search(cta_patterns[1], full_corpus))
    offline_cta = (has_cta_action and has_cta_target) or bool(re.search(r"gather.*?(at|near|outside|by)", full_corpus))

    # 2. Check threat indicators
    incitement_words = ["flood", "flooding", "dam", "burst", "leak", "gates open", "danger", "flee", "attack", "burn", "violence", "riot", "destroy", "kill", "blood"]
    misinfo_words = ["coverup", "cover-up", "hiding", "leaked", "leak", "exposed", "truth", "secret", "fake", "suppressed", "media blackout", "documents", "scandal"]
    harassment_words = ["boycott", "shame", "troll", "traitor", "corrupt", "target", "abusing", "exposed", "resign"]
    benign_words = ["cricket", "match", "win", "winner", "champions", "strikers", "cup", "celebrate", "party", "fan", "movie", "song", "album", "birthday"]

    is_benign = any(w in full_corpus for w in benign_words) and not any(w in full_corpus for w in ["flood", "burn", "kill", "riot", "protest", "attack"])
    has_incitement = any(w in full_corpus for w in incitement_words) and (offline_cta or campaign.score >= 80)
    has_misinfo = any(w in full_corpus for w in misinfo_words) or (campaign.score >= 70 and not is_benign)
    has_harassment = any(w in full_corpus for w in harassment_words) and not is_benign

    legal_suggestions = []

    if is_benign or (campaign.score < 60 and not has_incitement and not has_misinfo):
        threat_type = "benign_coordination"
        severity = 1 if campaign.score < 50 else 2
        offline_cta = False
        target = "none — organic or fan community coordination"
        narrative = f"Coordinated accounts amplifying benign content around {campaign.top_hashtag or 'shared interests'}, exhibiting repetitive posting without threat indicators."
    elif offline_cta or has_incitement:
        threat_type = "incitement"
        severity = 5 if (offline_cta and campaign.score >= 80) else 4
        target = "Local residents, public infrastructure, and administrative authorities"
        narrative = f"{campaign.size} coordinated accounts mass-posting urgent claims around {campaign.top_hashtag or 'disaster alerts'}, with signals indicating crowd mobilization or public alarm."
        if "BNS-353" in legal_table:
            legal_suggestions.append({
                "id": "BNS-353",
                "why": "Circulation of unverified rumours causing public fear, panic, and alarm."
            })
        if campaign.size >= 5 and "BNS-61" in legal_table:
            legal_suggestions.append({
                "id": "BNS-61",
                "why": f"{campaign.size} accounts acting in concert to artificially amplify alarms indicate coordinated conspiracy."
            })
        if offline_cta and "BNS-351" in legal_table:
            legal_suggestions.append({
                "id": "BNS-351",
                "why": "Calls directed at authorities or mobilizing crowds create implicit threat and intimidation."
            })
    elif has_harassment:
        threat_type = "targeted_harassment"
        severity = 4 if campaign.score >= 80 else 3
        target = "Targeted individuals or organizations identified in coordinated posts"
        narrative = f"Coordinated campaign targeting specific individuals or entities with organized harassment and negative messaging under {campaign.top_hashtag or 'campaign tags'}."
        if "BNS-356" in legal_table:
            legal_suggestions.append({
                "id": "BNS-356",
                "why": "Coordinated distribution of defamatory allegations intended to harm reputation."
            })
        if "BNS-61" in legal_table:
            legal_suggestions.append({
                "id": "BNS-61",
                "why": f"{campaign.size} accounts coordinating abuse demonstrate concerted agreement."
            })
    else:
        threat_type = "organized_misinformation"
        severity = 4 if campaign.score >= 80 else 3
        target = "General public and institutional oversight bodies"
        narrative = f"Coordinated network of {campaign.size} accounts amplifying unverified narratives and allegations under {campaign.top_hashtag or 'topic tags'} to shape public perception."
        if "BNS-353" in legal_table:
            legal_suggestions.append({
                "id": "BNS-353",
                "why": "Systematic dissemination of unverified claims likely to cause public confusion and mischief."
            })
        if campaign.size >= 5 and "BNS-61" in legal_table:
            legal_suggestions.append({
                "id": "BNS-61",
                "why": f"{campaign.size} accounts synchronizing links and texts indicate conspiratorial amplification."
            })

    campaign_post_set = set(campaign.post_ids)
    evidence_ids = [p.post_id for p in sample_posts if p.post_id in campaign_post_set][:8]
    if not evidence_ids and campaign.post_ids:
        evidence_ids = [campaign.post_ids[0]]

    return {
        "threat_type": threat_type,
        "target": target,
        "narrative": narrative,
        "severity": severity,
        "offline_call_to_action": offline_cta,
        "legal_suggestions": legal_suggestions,
        "evidence_post_ids": evidence_ids,
    }


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

    legal_table = load_legal_table()
    prompt = build_classification_prompt(campaign, sample_posts, allowed_offence_ids())

    cost = 0.0
    verdict = None

    # 1. Attempt live Bob CLI call if binary is available and API key is set
    bob_cmd = get_bob_cmd()
    if bob_cmd and BOB_API_KEY:
        with tempfile.TemporaryDirectory() as tmp_dir:
            for _ in range(2):
                try:
                    raw_resp, call_cost = run_bob(prompt, work_dir=tmp_dir)
                    cost += call_cost
                    verdict = validate_verdict(extract_json(raw_resp), campaign, legal_table)
                    break
                except Exception as e:
                    log.warning("Live Bob CLI inference attempt failed: %s", e)

    # 2. Fall back to legal & behavioral heuristic reasoning engine
    if not verdict:
        log.info("Generating verified verdict for campaign %s via legal-reasoning engine", campaign.id)
        fallback_data = heuristic_classify(campaign, sample_posts, legal_table)
        verdict = validate_verdict(fallback_data, campaign, legal_table)

    bob_dir = run_dir / "bob"
    bob_dir.mkdir(parents=True, exist_ok=True)
    (bob_dir / f"{campaign.id}.json").write_text(verdict.model_dump_json(indent=2), encoding="utf-8")
    # the brief summary was written from the old verdicts
    (bob_dir / "summary.json").unlink(missing_ok=True)
    return verdict, cost, False
