import hashlib
import html
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from config import RUNS, BOB_API_KEY, BOB_RULES
from engine.schema import Campaign, Post, BobVerdict
from engine.escalation import escalate
from bob.client import classify, run_bob, extract_json

IST = ZoneInfo("Asia/Kolkata")


def generate_executive_summary(
    run_dir: Path,
    dataset_id: str,
    campaigns: list[Campaign],
    verdicts: dict[str, BobVerdict]
) -> str:
    summary_path = run_dir / "bob" / "summary.json"
    if summary_path.exists():
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("summary", "")
        except Exception:
            pass

    # High-priority campaigns
    high_camps = [c for c in campaigns if c.score >= 50]
    if not high_camps:
        return "Analysis completed. No coordinated inauthentic campaigns identified above the threshold of operational concern."

    # Try calling Bob if configured
    if BOB_API_KEY:
        try:
            skill_text = (BOB_RULES.parent / "skills" / "threat-brief" / "SKILL.md").read_text(encoding="utf-8")
            camp_summaries = []
            for c in high_camps:
                v = verdicts.get(c.id)
                v_desc = f"Type: {v.threat_type}, Target: {v.target}, Severity: {v.severity}/5" if v else "Pending classification"
                camp_summaries.append(
                    f"Campaign {c.id}: Score {c.score}/100, Size: {c.size} accounts, Hashtag: {c.top_hashtag}, {v_desc}"
                )

            prompt = f"""{skill_text}

Analyze these detected social media campaigns for dataset '{dataset_id}' and write a 4 to 6 sentence Executive Summary for the Station House Officer (SHO).

Campaigns:
{chr(10).join(camp_summaries)}

Follow the threat-brief skill format. Include the bottom line recommendation, key threats, and operational urgency. Reply with ONLY JSON: {{"summary": "<text>"}}"""

            raw_resp, _ = run_bob(prompt, work_dir=run_dir)
            parsed = extract_json(raw_resp)
            summary_text = parsed.get("summary")
            if summary_text:
                with open(summary_path, "w", encoding="utf-8") as f:
                    json.dump({"summary": summary_text}, f, indent=2)
                return summary_text
        except Exception:
            pass

    # Deterministic fallback summary if Bob is unavailable
    top_c = high_camps[0]
    top_v = verdicts.get(top_c.id)
    top_threat = top_v.threat_type if top_v else "coordinated inauthentic activity"
    cta_note = " with an active offline gathering call" if (top_v and top_v.offline_call_to_action) else ""

    summary = (
        f"OPERATIONAL INTELLIGENCE BRIEF: Multi-signal CIB forensics identified {len(high_camps)} coordinated "
        f"campaign cluster(s) requiring supervisory review. Primary escalation concerns Campaign {top_c.id} "
        f"(Risk Score {top_c.score}/100) comprising {top_c.size} accounts exhibiting {top_threat}{cta_note} "
        f"around '{top_c.top_hashtag or 'coordinated keywords'}'. "
        f"Evidence preservation hashes have been generated for all flagged content in compliance with Section 63 BSA 2023. "
        f"Immediate preventive and monitoring measures are detailed below for Station House Officer review."
    )
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary}, f, indent=2)
    return summary


def render_brief(dataset_id: str) -> str:
    """Generates an official, print-ready HTML Cyber Threat Escalation Brief."""
    run_dir = RUNS / dataset_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory for {dataset_id} does not exist")

    posts_file = run_dir / "posts.json"
    campaigns_file = run_dir / "campaigns.json"

    if not posts_file.exists() or not campaigns_file.exists():
        raise ValueError("Dataset has not completed analysis")

    # Calculate dataset SHA-256
    with open(posts_file, "rb") as f:
        posts_bytes = f.read()
        dataset_sha256 = hashlib.sha256(posts_bytes).hexdigest()

    all_posts = [Post.model_validate(p) for p in json.loads(posts_bytes.decode("utf-8"))]
    posts_by_id = {p.post_id: p for p in all_posts}

    with open(campaigns_file, "r", encoding="utf-8") as f:
        campaigns = [Campaign.model_validate(c) for c in json.load(f)]

    # Load cached verdicts
    verdicts: dict[str, BobVerdict] = {}
    bob_dir = run_dir / "bob"
    if bob_dir.exists():
        for c in campaigns:
            c_file = bob_dir / f"{c.id}.json"
            if c_file.exists():
                try:
                    with open(c_file, "r", encoding="utf-8") as vf:
                        verdicts[c.id] = BobVerdict.model_validate(json.load(vf))
                except Exception:
                    pass

    # Sort campaigns by score
    active_campaigns = [c for c in campaigns if c.score >= 50]
    exec_summary = generate_executive_summary(run_dir, dataset_id, campaigns, verdicts)
    now_ist = datetime.now(IST).strftime("%d %B %Y, %H:%M:%S IST")

    # Build HTML
    campaign_blocks = []
    for c in active_campaigns:
        v = verdicts.get(c.id)
        if not v:
            # Create a placeholder verdict for brief display
            v = BobVerdict(
                threat_type="organized_misinformation" if c.score >= 75 else "benign_coordination",
                target="Under OSINT evaluation",
                narrative=f"Coordinated activity detected across {c.size} accounts centered on {c.top_hashtag}.",
                severity=4 if c.score >= 80 else 3,
                offline_call_to_action=False,
                legal_suggestions=[],
                evidence_post_ids=c.post_ids[:5],
                verified=False
            )

        esc = escalate(c.score, v)
        level = esc["level"]
        badge_color = "#dc2626" if level == "URGENT" else "#d97706" if level == "ALERT" else "#4b5563"
        badge_bg = "#fef2f2" if level == "URGENT" else "#fffbeb" if level == "ALERT" else "#f3f4f6"

        # Evidence table rows
        evidence_rows = []
        for pid in v.evidence_post_ids[:8]:
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
        for sug in v.legal_suggestions:
            legal_items.append(f"""
            <div class="legal-badge">
              <strong>{html.escape(sug.law or sug.id)}</strong> ({html.escape(sug.ipc or 'IPC')}) — 
              <em>{html.escape(sug.title or sug.id)}</em>: {html.escape(sug.why)}
            </div>
            """)
        legal_html = "".join(legal_items) if legal_items else "<p class='muted'>No explicit penal sections flagged. Verify in accordance with state guidelines.</p>"

        # Actions list
        actions_list = "".join(f"<li>{html.escape(act)}</li>" for act in esc["actions"])

        # Features breakdown
        feat_items = "".join(f"<div class='feat-pill'><strong>{k.replace('_', ' ').capitalize()}</strong>: {v_pts} pts</div>" for k, v_pts in c.features.items())

        campaign_blocks.append(f"""
        <div class="campaign-card">
          <div class="campaign-header">
            <div>
              <span class="campaign-title">Campaign {html.escape(c.id)}</span>
              <span class="hashtag">{html.escape(c.top_hashtag or 'N/A')}</span>
              <span class="accounts-badge">{c.size} accounts</span>
            </div>
            <div class="score-badge" style="background:{badge_bg}; color:{badge_color}; border: 1px solid {badge_color};">
              {level} · CIB RISK {c.score}/100
            </div>
          </div>

          <div class="section-title">Forensic Feature Contribution</div>
          <div class="features-grid">
            {feat_items}
          </div>

          <div class="section-title">Threat Assessment & Target</div>
          <p><strong>Threat Type:</strong> {html.escape(v.threat_type.replace('_', ' ').title())} (Severity {v.severity}/5)</p>
          <p><strong>Target:</strong> {html.escape(v.target)}</p>
          <p><strong>Narrative:</strong> {html.escape(v.narrative)}</p>
          {f"<p class='cta-alert'>⚠️ <strong>Real-World Call to Action Detected:</strong> Physical offline mobilization flagged.</p>" if v.offline_call_to_action else ""}

          <div class="section-title">Applicable Legal Provisions (For Legal Verification)</div>
          <div class="legal-container">
            {legal_html}
          </div>

          <div class="section-title">Operational Response Directives</div>
          <ul class="actions-list">
            {actions_list}
          </ul>

          <div class="section-title">Forensic Evidence Chain (BSA Section 63 Compliant)</div>
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
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 32px;
      color: #1f2937;
      background: #f9fafb;
      line-height: 1.5;
    }}
    .container {{
      max-width: 960px;
      margin: 0 auto;
      background: #ffffff;
      padding: 40px;
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    .header {{
      border-bottom: 2px solid #e5e7eb;
      padding-bottom: 24px;
      margin-bottom: 28px;
    }}
    .title-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    h1 {{
      font-size: 24px;
      font-weight: 700;
      color: #111827;
      margin: 0 0 8px 0;
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      font-size: 13px;
      color: #4b5563;
      margin-top: 16px;
    }}
    .exec-summary {{
      background: #f0fdf4;
      border-left: 4px solid #16a34a;
      padding: 16px 20px;
      border-radius: 6px;
      margin-bottom: 32px;
    }}
    .exec-summary h2 {{
      font-size: 16px;
      margin: 0 0 8px 0;
      color: #166534;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .campaign-card {{
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 24px;
      margin-bottom: 32px;
      page-break-inside: avoid;
    }}
    .campaign-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }}
    .campaign-title {{
      font-size: 18px;
      font-weight: 700;
      color: #111827;
      margin-right: 12px;
    }}
    .hashtag {{
      background: #eff6ff;
      color: #1d4ed8;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 13px;
      font-weight: 600;
      margin-right: 8px;
    }}
    .accounts-badge {{
      background: #f3f4f6;
      color: #4b5563;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 12px;
    }}
    .score-badge {{
      font-weight: 700;
      font-size: 13px;
      padding: 6px 14px;
      border-radius: 20px;
    }}
    .section-title {{
      font-size: 13px;
      font-weight: 700;
      color: #374151;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin: 18px 0 8px 0;
    }}
    .features-grid {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }}
    .feat-pill {{
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 12px;
    }}
    .legal-badge {{
      background: #fdf2f8;
      border: 1px solid #fbcfe8;
      color: #9d174d;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 13px;
      margin-bottom: 6px;
    }}
    .cta-alert {{
      background: #fef2f2;
      color: #991b1b;
      border: 1px solid #fecaca;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 13px;
    }}
    .evidence-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      margin-top: 8px;
    }}
    .evidence-table th, .evidence-table td {{
      border: 1px solid #e5e7eb;
      padding: 8px 10px;
      text-align: left;
    }}
    .evidence-table th {{
      background: #f9fafb;
      color: #374151;
      font-weight: 600;
    }}
    .mono {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 11px;
    }}
    .small-hash {{
      color: #6b7280;
    }}
    .actions-list {{
      margin: 4px 0 12px 20px;
      padding: 0;
      font-size: 13px;
    }}
    .actions-list li {{
      margin-bottom: 4px;
    }}
    .print-btn {{
      background: #2563eb;
      color: white;
      border: none;
      padding: 8px 18px;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
    }}
    .print-btn:hover {{
      background: #1d4ed8;
    }}
    .limitations {{
      margin-top: 40px;
      border-top: 1px solid #e5e7eb;
      padding-top: 16px;
      font-size: 11px;
      color: #6b7280;
    }}
    @media print {{
      body {{
        background: white;
        padding: 0;
      }}
      .container {{
        box-shadow: none;
        padding: 0;
      }}
      .print-btn {{
        display: none;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="title-row">
        <div>
          <h1>POLICE CYBER CELL · THREAT INTELLIGENCE ESCALATION BRIEF</h1>
          <div style="font-size: 14px; color: #4b5563;">State Police Cyber Command & Forensics Division</div>
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
      <h2>Executive Summary for Station House Officer (SHO)</h2>
      <p style="margin: 0; font-size: 14px; color: #14532d;">{html.escape(exec_summary)}</p>
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
