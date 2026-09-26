import hashlib
import html
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from config import RUNS, BOB_API_KEY
from engine.schema import Campaign, Post, BobVerdict
from engine.escalation import escalate
from bob.client import cached_verdict, run_bob, extract_json

IST = ZoneInfo("Asia/Kolkata")
MAX_CAMPAIGNS = 10  # brief length cap; the dashboard lists every campaign
# same wording and severity colours as the dashboard (docs/design-system.md)
LEVEL_COLORS = {"URGENT": ("#c21f2b", "#fdecee"), "ALERT": ("#a45f00", "#fdf3e1"), "MONITOR": ("#3b6285", "#e9f1f8")}
FEATURE_LABELS = {
    "speed": "Posted within seconds", "duplication": "Near-identical text", "multi_signal": "Several signals",
    "fresh_accounts": "New accounts", "burst": "Sudden burst", "concentration": "Same hashtag or link",
}
log = logging.getLogger(__name__)


def generate_executive_summary(
    run_dir: Path,
    dataset_id: str,
    campaigns: list[Campaign],
    verdicts: dict[str, BobVerdict]
) -> str:
    """Bob writes the summary from the campaigns and verified verdicts; only Bob's text is cached."""
    summary_path = run_dir / "bob" / "summary.json"
    if summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8")).get("summary", "")

    if not campaigns:
        return "Analysis completed. No coordinated campaigns were detected in this dataset."

    camp_lines = []
    for c in campaigns[:MAX_CAMPAIGNS]:
        v = verdicts.get(c.id)
        v_desc = (f"Type: {v.threat_type}, Target: {v.target}, Severity: {v.severity}/5, "
                  f"Escalation: {escalate(c.score, v)['level']}") if v else "Not yet classified by IBM Bob"
        camp_lines.append(f"Campaign {c.id}: Score {c.score}/100, Size: {c.size} accounts, Hashtag: {c.top_hashtag}, {v_desc}")

    if BOB_API_KEY:
        try:
            prompt = f"""You are a police cyber cell analyst. Write a 4 to 6 sentence Executive Summary for a busy Station House Officer (SHO)
about the coordinated social media campaigns detected in dataset '{dataset_id}'. Plain English, no jargon.

Start with a one-line bottom line: the most urgent campaign and its escalation level. Then the key threats, any real-world
call to gather, and how urgent action is. Do not suggest legal sections. End by noting this is automated decision support.
Use only the facts below. Do not invent threat types for campaigns that are not yet classified.
Do not use any tools and do not read any files: everything you need is here.

Campaigns:
{chr(10).join(camp_lines)}

Reply with ONLY JSON: {{"summary": "<text>"}}"""
            with tempfile.TemporaryDirectory() as tmp_dir:
                raw_resp, _ = run_bob(prompt, work_dir=tmp_dir,
                                      instruction="Write the executive summary described on stdin. Follow its instructions exactly.")
            summary_text = extract_json(raw_resp).get("summary")
            if summary_text:
                summary_path.parent.mkdir(parents=True, exist_ok=True)
                summary_path.write_text(json.dumps({"summary": summary_text}, indent=2), encoding="utf-8")
                return summary_text
        except Exception:
            log.exception("Bob summary failed; using the rule-based summary")

    # Rule-based summary when Bob is unavailable (not cached, so Bob is tried again next time)
    top_c = campaigns[0]
    top_v = verdicts.get(top_c.id)
    classified = sum(1 for c in campaigns if c.id in verdicts)
    top_desc = (f"classified by IBM Bob as {top_v.threat_type.replace('_', ' ')} "
                f"(escalation {escalate(top_c.score, top_v)['level']})") if top_v else "not yet classified by IBM Bob"
    return (
        f"Coordination analysis detected {len(campaigns)} campaign(s); {classified} classified by IBM Bob. "
        f"Highest risk is Campaign {top_c.id} (CIB score {top_c.score}/100, {top_c.size} accounts, "
        f"'{top_c.top_hashtag or 'no hashtag'}'), {top_desc}. "
        f"Evidence posts are hashed with SHA-256 below to support a Section 63 BSA certificate. "
        f"Recommended actions per campaign follow for SHO review."
    )


def threat_html(v: BobVerdict | None) -> str:
    if not v:
        return "<p class='muted'>Not yet classified by IBM Bob.</p>"
    cta = ("<p class='cta-alert'>⚠️ <strong>Real-World Call to Action Detected:</strong> Physical offline mobilization flagged.</p>"
           if v.offline_call_to_action else "")
    return (f"<p><strong>Threat Type:</strong> {html.escape(v.threat_type.replace('_', ' ').title())} (Severity {v.severity}/5)</p>"
            f"<p><strong>Target:</strong> {html.escape(v.target)}</p>"
            f"<p><strong>Narrative:</strong> {html.escape(v.narrative)}</p>{cta}")


def render_brief(dataset_id: str) -> str:
    """Generates an official, print-ready HTML Cyber Threat Escalation Brief."""
    run_dir = RUNS / dataset_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory for {dataset_id} does not exist")

    posts_file = run_dir / "posts.json"
    campaigns_file = run_dir / "campaigns.json"

    if not posts_file.exists() or not campaigns_file.exists():
        raise FileNotFoundError("Dataset has not completed analysis")

    # Dataset SHA-256, read in chunks (posts.json can be 100+ MB)
    sha = hashlib.sha256()
    with open(posts_file, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
    dataset_sha256 = sha.hexdigest()

    # Evidence comes from each campaign's first posts (Bob only sees and cites these)
    samples_file = run_dir / "samples.json"
    if not samples_file.exists():
        raise FileNotFoundError("This dataset was analysed by an older version. Run the analysis again.")
    samples = json.loads(samples_file.read_text(encoding="utf-8"))
    posts_by_id = {p["post_id"]: Post.model_validate(p) for posts in samples.values() for p in posts}

    with open(campaigns_file, "r", encoding="utf-8") as f:
        campaigns = [Campaign.model_validate(c) for c in json.load(f)]

    verdicts = {c.id: v for c in campaigns if (v := cached_verdict(run_dir, c.id))}

    shown = campaigns[:MAX_CAMPAIGNS]
    exec_summary = generate_executive_summary(run_dir, dataset_id, campaigns, verdicts)
    now_ist = datetime.now(IST).strftime("%d %B %Y, %H:%M:%S IST")

    # Build HTML
    campaign_blocks = []
    for c in shown:
        v = verdicts.get(c.id)
        if v:
            esc = escalate(c.score, v)
            level, actions, evidence_ids = esc["level"], esc["actions"], v.evidence_post_ids
        else:
            # Not classified yet: no threat type or escalation is guessed; show sample posts as evidence
            level, actions = "PENDING", ["Classify this campaign with IBM Bob in the dashboard before escalating"]
            evidence_ids = [p["post_id"] for p in samples.get(c.id, [])[:5]]
        badge_color, badge_bg = LEVEL_COLORS.get(level, ("#5c6470", "#f0f2f5"))

        # Evidence table rows
        evidence_rows = []
        for pid in evidence_ids[:8]:
            p = posts_by_id.get(pid)
            if not p:
                continue
            post_time = datetime.fromtimestamp(p.created_at, tz=IST).strftime("%d-%b %H:%M:%S")
            p_bytes = json.dumps(p.model_dump(), sort_keys=True).encode("utf-8")
            p_hash = hashlib.sha256(p_bytes).hexdigest()[:16] + "..."
            evidence_rows.append(f"""
            <tr>
              <td class="mono">{html.escape(p.post_id)}</td>
              <td>{html.escape(post_time)}</td>
              <td class="mono">{html.escape(p.username)}</td>
              <td>{html.escape(p.text)}</td>
              <td class="mono small-hash" title="{hashlib.sha256(p_bytes).hexdigest()}">{html.escape(p_hash)}</td>
            </tr>
            """)

        # Legal suggestions
        legal_items = []
        for sug in (v.legal_suggestions if v else []):
            legal_items.append(f"""
            <div class="legal-badge">
              <strong>{html.escape(sug.law or sug.id)}</strong> ({html.escape(sug.ipc or 'IPC')}) — 
              <em>{html.escape(sug.title or sug.id)}</em>: {html.escape(sug.why)}
            </div>
            """)
        legal_html = "".join(legal_items) if legal_items else "<p class='muted'>No explicit penal sections flagged. Verify in accordance with state guidelines.</p>"

        # Actions list
        actions_list = "".join(f"<li>{html.escape(act)}</li>" for act in actions)

        # Features breakdown
        feat_items = "".join(f"<div class='feat-pill'>{FEATURE_LABELS.get(k, k)}: <strong>{v_pts}</strong></div>" for k, v_pts in c.features.items())

        campaign_blocks.append(f"""
        <div class="campaign-card">
          <div class="campaign-header">
            <div>
              <span class="campaign-title">Campaign {html.escape(c.id)}</span>
              <span class="hashtag">{html.escape(c.top_hashtag or 'N/A')}</span>
              <span class="accounts-badge">{c.size} accounts</span>
            </div>
            <div class="score-badge" style="background:{badge_bg}; color:{badge_color}; border: 1px solid {badge_color};">
              {level.capitalize()} · coordination score {c.score}/100
            </div>
          </div>

          <div class="section-title">Why it was flagged (points)</div>
          <div class="features-grid">
            {feat_items}
          </div>

          <div class="section-title">IBM Bob assessment</div>
          {threat_html(v)}

          <div class="section-title">Legal sections to check (verify with a legal officer)</div>
          <div class="legal-container">
            {legal_html}
          </div>

          <div class="section-title">Recommended actions</div>
          <ul class="actions-list">
            {actions_list}
          </ul>

          <div class="section-title">Forensic Evidence Chain (BSA Section 63 Compliant){"" if v else " — sample posts"}</div>
          <table class="evidence-table">
            <thead>
              <tr>
                <th>Post ID</th>
                <th>Timestamp (IST)</th>
                <th>Handle</th>
                <th>Content Text</th>
                <th>SHA-256 Hash</th>
              </tr>
            </thead>
            <tbody>
              {''.join(evidence_rows)}
            </tbody>
          </table>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Cyber Threat Intelligence Escalation Brief — {html.escape(dataset_id)}</title>
  <style>
    /* "Case File" design language (docs/design-system.md), light document for print */
    :root {{ --ink: #15181d; --muted: #5c6470; --line: #e2e5ea; --subtle: #f0f2f5; --accent: #2456d6; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; margin: 0; padding: 32px 16px;
           color: var(--ink); background: #f6f7f9; line-height: 1.5; font-size: 14px; }}
    .container {{ max-width: 900px; margin: 0 auto; background: #fff; padding: 40px; border: 1px solid var(--line); border-radius: 8px; }}
    .header {{ border-bottom: 1px solid var(--line); padding-bottom: 20px; margin-bottom: 24px; }}
    .title-row {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }}
    .eyebrow, .section-title, .exec-summary h2 {{ font-size: 12px; font-weight: 500; letter-spacing: .04em; text-transform: uppercase; color: var(--muted); }}
    h1 {{ font-size: 22px; font-weight: 600; margin: 4px 0 0; }}
    .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px 24px; font-size: 13px; color: var(--muted); margin-top: 16px; }}
    .meta-grid strong {{ color: var(--ink); font-weight: 500; }}
    .exec-summary {{ border-left: 3px solid var(--accent); background: var(--subtle); padding: 14px 18px; border-radius: 0 6px 6px 0; margin-bottom: 28px; }}
    .exec-summary h2 {{ margin: 0 0 6px; }}
    .exec-summary p {{ margin: 0; }}
    .campaign-card {{ border: 1px solid var(--line); border-radius: 8px; padding: 20px; margin-bottom: 20px; break-inside: avoid; }}
    .campaign-header {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }}
    .campaign-title {{ font-size: 16px; font-weight: 600; margin-right: 8px; }}
    .hashtag, .accounts-badge {{ font-size: 13px; color: var(--muted); margin-right: 8px; }}
    .score-badge {{ font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 999px; white-space: nowrap; }}
    .section-title {{ margin: 18px 0 8px; }}
    .features-grid {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .feat-pill {{ font-size: 12px; background: var(--subtle); border-radius: 999px; padding: 2px 10px; }}
    p {{ margin: 4px 0; }}
    .muted {{ color: var(--muted); }}
    .legal-badge {{ background: var(--subtle); border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; font-size: 13px; }}
    .cta-alert {{ background: #fdecee; color: #c21f2b; border-radius: 6px; padding: 8px 12px; }}
    .actions-list {{ margin: 0; padding-left: 20px; }}
    .evidence-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    .evidence-table th {{ text-align: left; font-weight: 500; color: var(--muted); background: var(--subtle); padding: 6px 8px; }}
    .evidence-table td {{ border-top: 1px solid var(--line); padding: 6px 8px; vertical-align: top; }}
    .mono {{ font-family: ui-monospace, "Cascadia Mono", Consolas, monospace; }}
    .small-hash {{ color: var(--muted); }}
    .print-btn {{ background: var(--accent); color: #fff; border: 0; border-radius: 6px; padding: 8px 14px; font-size: 13px; font-weight: 500; cursor: pointer; }}
    .limitations {{ border-top: 1px solid var(--line); padding-top: 16px; margin-top: 24px; font-size: 12px; color: var(--muted); }}
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .container {{ border: 0; padding: 0; }}
      .print-btn {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="title-row">
        <div>
          <div class="eyebrow">Police cyber cell · for the Station House Officer</div>
          <h1>Threat escalation brief</h1>
        </div>
        <button class="print-btn" onclick="window.print()">Print / Save PDF</button>
      </div>

      <div class="meta-grid">
        <div><strong>Dataset Reference:</strong> {html.escape(dataset_id)}</div>
        <div><strong>Generated Timestamp:</strong> {html.escape(now_ist)}</div>
        <div><strong>Evidence SHA-256:</strong> <span class="mono">{html.escape(dataset_sha256[:20])}...</span></div>
        <div><strong>Compliance Standard:</strong> Bharatiya Sakshya Adhiniyam (BSA) Section 63</div>
      </div>
    </div>

    <div class="exec-summary">
      <h2>Summary</h2>
      <p>{html.escape(exec_summary)}</p>
    </div>

    <div class="campaigns-section">
      {''.join(campaign_blocks)}
    </div>

    <div class="limitations">
      <strong>Operational Notice & Legal Limitations:</strong> This threat intelligence brief is generated by automated behavioral coordination analysis (coordination-network-toolkit, NetworkX Louvain) and AI legal reasoning (IBM Bob). All identified campaigns, classifications, and statutory provisions are decision-support indicators intended solely for guidance and must be independently verified by an investigating officer and verified by a designated legal officer before taking penal or administrative action.
    </div>
  </div>
</body>
</html>
"""
    # Write to run_dir/brief.html
    (run_dir / "brief.html").write_text(html_content, encoding="utf-8")
    return html_content
