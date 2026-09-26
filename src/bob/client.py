import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from config import BOB_API_KEY, BOB_MAX_COST, BOB_RULES
from engine.schema import Campaign, Post, BobVerdict
from bob.legal import load_legal_table, allowed_offence_ids


class BobNotConfigured(Exception):
    pass


def get_bob_cmd() -> list[str]:
    appdata = os.environ.get("APPDATA", "")
    bob_js = Path(appdata) / "npm/node_modules/bobshell/dist/bob.js"
    if bob_js.exists():
        return ["node", str(bob_js)]
    bob_bin = shutil.which("bob")
    if bob_bin:
        return [bob_bin]
    return ["bob"]


def run_bob(
    prompt: str,
    work_dir: Path | str,
    instruction: str = "Classify the campaign described on stdin. Follow its instructions exactly.",
    max_cost: str = BOB_MAX_COST,
) -> tuple[str, float]:
    """Runs a headless Bob inference call via CLI with JSON output format. The prompt goes via stdin."""
    bob_cmd = get_bob_cmd()
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


def classify(
    run_dir: Path,
    campaign: Campaign,
    sample_posts: list[Post]
) -> tuple[BobVerdict, float, bool]:
    """
    Classifies a coordinated campaign using IBM Bob with schema validation,
    legal table filtering, and disk caching.
    Returns (verdict, cost, is_cached). Raises instead of guessing if Bob gives no valid answer.
    """
    run_dir = Path(run_dir)
    verdict = cached_verdict(run_dir, campaign.id)
    if verdict:
        return verdict, 0.0, True

    if not BOB_API_KEY:
        raise BobNotConfigured("IBM Bob API key is not configured and no cached verdict exists.")

    legal_table = load_legal_table()
    prompt = build_classification_prompt(campaign, sample_posts, allowed_offence_ids())

    cost, error = 0.0, None
    with tempfile.TemporaryDirectory() as tmp_dir:
        for _ in range(2):
            try:
                raw_resp, call_cost = run_bob(prompt, work_dir=tmp_dir)
                cost += call_cost
                verdict = validate_verdict(extract_json(raw_resp), campaign, legal_table)
                break
            except Exception as e:  # Bob error, bad JSON or failed validation: retry once
                error = e
        else:
            raise RuntimeError(f"IBM Bob did not return a valid verdict: {error}")

    bob_dir = run_dir / "bob"
    bob_dir.mkdir(parents=True, exist_ok=True)
    (bob_dir / f"{campaign.id}.json").write_text(verdict.model_dump_json(indent=2), encoding="utf-8")
    # the brief summary was written from the old verdicts
    (bob_dir / "summary.json").unlink(missing_ok=True)
    return verdict, cost, False
