import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from config import BOB_API_KEY, BOB_MAX_COST, BOB_RULES
from engine.schema import Campaign, Post, BobVerdict, LegalSuggestion
from bob.legal import load_legal_table, allowed_offence_ids


def get_bob_cmd() -> list[str]:
    appdata = os.environ.get("APPDATA", "")
    bob_js = Path(appdata) / "npm/node_modules/bobshell/dist/bob.js"
    if bob_js.exists():
        return ["node", str(bob_js)]
    bob_bin = shutil.which("bob")
    if bob_bin:
        return [bob_bin]
    return ["bob"]


def run_bob(prompt: str, work_dir: Path | str, max_cost: str = BOB_MAX_COST) -> tuple[str, float]:
    """Runs a headless Bob inference call via CLI with JSON output format."""
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
        "Classify the campaign described on stdin. Follow its instructions exactly."
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

    try:
        data = json.loads(res.stdout)
        last_message = data.get("last_message", "")
        cost = float(data.get("stats", {}).get("session_costs", 0.0))
        return last_message, cost
    except Exception as e:
        raise ValueError(f"Failed to parse Bob JSON response: {e}\nRaw stdout: {res.stdout[:500]}")


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
    cache_dir = run_dir / "bob"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{campaign.id}.json"

    # 1. Return cached verdict if present
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return BobVerdict.model_validate(data), 0.0, True

    # Check API key
    if not BOB_API_KEY:
        raise ValueError("IBM Bob API key is not configured and no cached verdict exists.")

    allowed_ids = allowed_offence_ids()
    legal_table = load_legal_table()
    prompt = build_classification_prompt(campaign, sample_posts, allowed_ids)

    # 2. Call Bob with retry logic
    parsed_json = None
    cost = 0.0
    verified = True

    with tempfile.TemporaryDirectory() as tmp_dir:
        for attempt in range(2):
            try:
                raw_resp, call_cost = run_bob(prompt, work_dir=tmp_dir)
                cost += call_cost
                parsed_json = extract_json(raw_resp)
                break
            except Exception:
                if attempt == 1:
                    verified = False

    if not parsed_json:
        # Fallback heuristic verdict if parsing completely failed
        parsed_json = {
            "threat_type": "organized_misinformation" if campaign.score >= 70 else "benign_coordination",
            "target": "General public",
            "narrative": f"Suspicious activity detected around {campaign.top_hashtag}",
            "severity": 3,
            "offline_call_to_action": False,
            "legal_suggestions": [],
            "evidence_post_ids": [p.post_id for p in sample_posts[:3]],
        }
        verified = False

    # 3. Filter legal suggestions to allowed offence IDs and enrich with law/ipc/title
    valid_suggestions = []
    for sug in parsed_json.get("legal_suggestions", []):
        sug_id = sug.get("id")
        if sug_id in legal_table and legal_table[sug_id]["kind"] == "offence":
            info = legal_table[sug_id]
            valid_suggestions.append(LegalSuggestion(
                id=sug_id,
                why=sug.get("why", "Associated with coordinated activity"),
                title=info["title"],
                law=info["law"],
                ipc=info["ipc"]
            ))

    # 4. Filter evidence post IDs to those belonging to the campaign
    campaign_post_set = set(campaign.post_ids) | {p.post_id for p in sample_posts}
    valid_evidence = [
        pid for pid in parsed_json.get("evidence_post_ids", [])
        if pid in campaign_post_set
    ]
    if not valid_evidence and sample_posts:
        valid_evidence = [sample_posts[0].post_id]

    verdict = BobVerdict(
        threat_type=parsed_json.get("threat_type", "organized_misinformation"),
        target=parsed_json.get("target", "Public"),
        narrative=parsed_json.get("narrative", ""),
        severity=int(parsed_json.get("severity", 3)),
        offline_call_to_action=bool(parsed_json.get("offline_call_to_action", False)),
        legal_suggestions=valid_suggestions,
        evidence_post_ids=valid_evidence,
        verified=verified
    )

    # 5. Save to disk cache
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(verdict.model_dump(), f, indent=2)

    return verdict, cost, False
