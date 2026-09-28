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
from engine.zones import dataset_zone, local_text, zone_abbr
from bob.client import cached_verdict, run_bob, extract_json

IST = ZoneInfo("Asia/Kolkata")  # the brief is generated for an Indian police unit
# ponytail: the dataset's display zone, set per render; two briefs rendered at the same instant could mix zones
ZONE = IST
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
                  f"Escalation: {escalate(c.score, v, ZONE)['level']}") if v else "Not yet classified by IBM Bob"
        if v and v.offline_event and v.offline_event.at:
            ev = v.offline_event
            v_desc += f", Planned offline gathering: {ev.what} at {ev.where} on {local_text(ev.at, ZONE, '%a %d %b %H:%M')}"
        spread = " -> ".join(p["name"] for p in c.platform_path)
        v_desc += f", Spread across: {spread}" if spread else ""
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


def clock(ts: int) -> str:
    return datetime.fromtimestamp(ts, ZONE).strftime("%H:%M")


def gap(seconds: int) -> str:
    m = max(0, round(seconds / 60))
    return f"{m} min" if m < 60 else f"{m // 60} h {m % 60} m"


PLATFORM_NAMES = {"x": "X", "whatsapp": "WhatsApp", "facebook": "Facebook", "telegram": "Telegram", "instagram": "Instagram"}


def strip_svg(c: Campaign, event_at: int, batch_end: int) -> str:
    """A static incident strip: first post → flagged → last post in the batch → planned gathering."""
    start, end = c.first_seen, max(event_at, batch_end)
    x = lambda t: 20 + (t - start) / max(1, end - start) * 560
    marks = [(c.first_seen, "first post", "#0072B2"), (c.detected_at, "flagged", "#1f7a3d"),
             (batch_end, "last post", "#8b929c"), (event_at, "gathering", "#c21f2b")]
    parts = [f'<line x1="20" y1="30" x2="580" y2="30" stroke="#e2e5ea" stroke-width="4" />',
             f'<rect x="{x(batch_end):.0f}" y="26" width="{580 - x(batch_end):.0f}" height="8" fill="#f0f2f5" />']
    for i, (t, label, color) in enumerate(m for m in marks if m[0]):
        y = 14 if i % 2 == 0 else 52
        parts.append(f'<circle cx="{x(t):.0f}" cy="30" r="6" fill="{color}" />'
                     f'<text x="{x(t):.0f}" y="{y}" text-anchor="middle" font-size="11" fill="{color}">{label} {clock(t)}</text>')
    return f'<svg viewBox="0 0 600 60" width="100%" height="60" role="img">{"".join(parts)}</svg>'


def threats_html(campaigns: list[Campaign], verdicts: dict[str, BobVerdict], batch_end: int) -> str:
    """Top-of-brief box for every planned offline gathering IBM Bob found (place quoted from the posts)."""
    rows = []
    for c in sorted((c for c in campaigns if c.id in verdicts and verdicts[c.id].offline_event),
                    key=lambda c: verdicts[c.id].offline_event.at or 0):
        ev = verdicts[c.id].offline_event
        if not ev.at:
            continue
        lead = f"Flagged at {clock(c.detected_at)}, <strong>{gap(ev.at - c.detected_at)} before</strong> the gathering. " if c.detected_at else ""
        rows.append(f"""
        <div class="threat-box">
          <div class="eyebrow" style="color:#c21f2b">Planned offline gathering · called by campaign {html.escape(c.id)}</div>
          <div class="threat-main">📍 {html.escape(ev.where)} &nbsp; 🕕 {local_text(ev.at, ZONE, "%a %d %b, %H:%M")}</div>
          <div>{html.escape(ev.what)}. Posts say “{html.escape(ev.where_quote)}”.</div>
          <div class="muted">{lead}{gap(ev.at - batch_end)} left after the last post in this batch.</div>
          {strip_svg(c, ev.at, batch_end)}
        </div>""")
    return "".join(rows)


def spread_html(c: Campaign) -> str:
    platforms = " → ".join(f"{PLATFORM_NAMES.get(p['name'], p['name'])} {clock(p['first_seen'])}" for p in c.platform_path)
    towns = " → ".join(f"{t['name']} {clock(t['first_seen'])}" for t in c.town_path)
    seeds = "; ".join(
        f"{html.escape(s['username'])} ({PLATFORM_NAMES.get(s['platform'], s['platform'] or '?')}, {clock(s['first_seen'])}"
        + (f", account {s['account_age_days']} days old" if s.get("account_age_days") is not None else "") + ")"
        for s in c.seeds)
    lines = [f"<p><strong>Platforms:</strong> {html.escape(platforms)}</p>" if platforms else "",
             f"<p><strong>Towns:</strong> {html.escape(towns)}</p>" if towns else "",
             f"<p><strong>Started by:</strong> {seeds}</p>" if seeds else "",
             f"<p><strong>Flagged by the detection rule at:</strong> {clock(c.detected_at)}</p>" if c.detected_at else ""]
    return "".join(lines) or "<p class='muted'>No platform or town information in this dataset.</p>"


def threat_html(v: BobVerdict | None) -> str:
    if not v:
        return "<p class='muted'>Not yet classified by IBM Bob.</p>"
    ev = v.offline_event
    if ev and ev.at:
        cta = (f"<p class='cta-alert'>⚠️ <strong>Call to gather:</strong> {html.escape(ev.where)}, "
               f"{local_text(ev.at, ZONE, '%d %b %H:%M')}. {html.escape(ev.what)}.</p>")
    else:
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
    global ZONE
    ZONE = dataset_zone(run_dir)

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
    timeline = json.loads((run_dir / "timeline.json").read_text(encoding="utf-8"))
    batch_end = timeline["points"][-1]["t"] + timeline["bucket_seconds"] if timeline["points"] else 0
    threats = threats_html(campaigns, verdicts, batch_end)
    exec_summary = generate_executive_summary(run_dir, dataset_id, campaigns, verdicts)
    now_ist = datetime.now(IST).strftime("%d %B %Y, %H:%M:%S IST")

    # Build HTML
    campaign_blocks = []
    for c in shown:
        v = verdicts.get(c.id)
        if v:
            esc = escalate(c.score, v, ZONE)
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
            post_time = datetime.fromtimestamp(p.created_at, tz=ZONE).strftime("%d-%b %H:%M:%S")
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

          <div class="section-title">How it spread</div>
          {spread_html(c)}

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

          <div class="section-title">Evidence records{"" if v else " — sample posts"}</div>
          <table class="evidence-table">
            <thead>
              <tr>
                <th>Post ID</th>
                <th>Timestamp ({zone_abbr(ZONE, batch_end)})</th>
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
    .threat-box {{ border: 1px solid #f3c4c8; border-left: 4px solid #c21f2b; background: #fdf6f7; border-radius: 0 8px 8px 0;
                  padding: 14px 18px; margin-bottom: 16px; break-inside: avoid; }}
    .threat-main {{ font-size: 20px; font-weight: 600; margin: 4px 0; }}
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
      </div>
    </div>

    {threats}

    <div class="exec-summary">
      <h2>Summary</h2>
      <p>{html.escape(exec_summary)}</p>
    </div>

    <div class="campaigns-section">
      {''.join(campaign_blocks)}
    </div>

    <div class="limitations">
      <strong>Operational Notice & Limitations:</strong> This is automated decision support (coordination-network-toolkit, NetworkX Louvain, IBM Bob), not a finding of inauthenticity, intent, imminent violence or legal liability. Coordination and model-generated claims require independent verification by an investigating officer. Hashes support integrity checking but do not by themselves establish chain of custody, certification or legal admissibility. Legal provisions are suggestions to check and require review by a legal officer before any action.
    </div>
  </div>
</body>
</html>
"""
    # Write to run_dir/brief.html
    (run_dir / "brief.html").write_text(html_content, encoding="utf-8")
    return html_content
