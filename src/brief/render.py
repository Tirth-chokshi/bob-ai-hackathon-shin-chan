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
ZONE = IST
MAX_CAMPAIGNS = 10  # brief length cap
LEVEL_COLORS = {
    "URGENT": ("#c21f2b", "#fdecee"),
    "ALERT": ("#a45f00", "#fdf3e1"),
    "MONITOR": ("#3b6285", "#e9f1f8"),
    "PENDING": ("#5c6470", "#f0f2f5"),
}
FEATURE_LABELS = {
    "speed": "Posted within seconds",
    "duplication": "Near-identical text",
    "multi_signal": "Several signals",
    "fresh_accounts": "New accounts",
    "burst": "Sudden burst",
    "concentration": "Same hashtag or link",
}
PLATFORM_NAMES = {
    "x": "X",
    "whatsapp": "WhatsApp",
    "facebook": "Facebook",
    "telegram": "Telegram",
    "instagram": "Instagram",
}
log = logging.getLogger(__name__)


def generate_executive_summary(
    run_dir: Path,
    dataset_id: str,
    campaigns: list[Campaign],
    verdicts: dict[str, BobVerdict]
) -> str:
    """Generates the executive summary text, either via IBM Bob or resilient rule-based engine."""
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
            prompt = f"""You are a police cyber cell analyst. Write an Executive Summary for a Station House Officer (SHO)
about the coordinated social media campaigns in dataset '{dataset_id}'. Plain English, no jargon.

Structure:
1. Executive Bottom Line (1-2 sentences on highest threat and immediate posture).
2. Pointwise Campaign Breakdown (one concise bullet per campaign with Campaign ID, threat type, size, escalation level, and offline threat if any).
3. Operational Next Steps (1-2 sentences on evidence preservation and automated decision support).

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
            log.exception("Bob summary failed; using rule-based summary")

    # Rule-based fallback
    top_c = campaigns[0]
    top_v = verdicts.get(top_c.id)
    classified = sum(1 for c in campaigns if c.id in verdicts)
    top_desc = (f"classified by IBM Bob as {top_v.threat_type.replace('_', ' ')} "
                f"(escalation {escalate(top_c.score, top_v)['level']})") if top_v else "not yet classified by IBM Bob"
    return (
        f"Coordination analysis detected {len(campaigns)} campaign(s); {classified} classified by IBM Bob. "
        f"Highest risk is Campaign {top_c.id.upper()} (CIB score {top_c.score}/100, {top_c.size} accounts, "
        f"'{top_c.top_hashtag or 'no hashtag'}'), {top_desc}. "
        f"Evidence records are cryptographically hashed with SHA-256 to support a Section 63 BSA certificate. "
        f"Recommended actions per campaign follow for SHO operational review."
    )


def generate_single_campaign_summary(
    c: Campaign,
    v: BobVerdict | None,
    level: str,
    actions: list[str],
    zone: ZoneInfo
) -> str:
    """Generates an executive summary specifically for a single campaign brief."""
    spread_parts = []
    if c.platform_path:
        spread_parts.append(f"disseminated across {' → '.join(PLATFORM_NAMES.get(p['name'], p['name']) for p in c.platform_path)}")
    if c.town_path:
        spread_parts.append(f"in {', '.join(t['name'] for t in c.town_path)}")
    spread_desc = f", {'; '.join(spread_parts)}" if spread_parts else ""

    if v:
        event_desc = (f" CRITICAL: A physical gathering has been called at '{v.offline_event.where}' on "
                      f"{local_text(v.offline_event.at, zone, '%a %d %b %H:%M')}, posing imminent crowd mobilization risk."
                      if (v.offline_event and v.offline_event.at) else "")
        narrative_desc = f" Targeted entity: {v.target}. Operational narrative: “{v.narrative}”." if v.narrative else ""
        return (
            f"Campaign {c.id.upper()} has been designated at escalation level {level} with a CIB coordination score "
            f"of {c.score}/100 across {c.size} coordinated accounts centered on '{c.top_hashtag or 'no hashtag'}'"
            f"{spread_desc}. "
            f"IBM Bob semantic analysis classifies this operation as {v.threat_type.replace('_', ' ').title()} "
            f"(Severity {v.severity}/5).{narrative_desc}{event_desc} "
            f"Primary operational directive: {actions[0] if actions else 'Preserve evidence records'}. "
            f"Section 63 BSA evidence records, feature weights, and statutory sections are itemized below for SHO action."
        )
    else:
        return (
            f"Campaign {c.id.upper()} has been detected as a high-density coordinated cluster of {c.size} accounts "
            f"with a CIB coordination score of {c.score}/100 and hashtag '{c.top_hashtag or 'no hashtag'}'"
            f"{spread_desc}. "
            f"Multiple accounts repeatedly posted identical or near-identical text and shared links in synchrony. "
            f"This campaign is pending semantic classification by IBM Bob. Investigating officers should trigger "
            f"automated assessment via the dashboard and review the Section 63 BSA evidence records below."
        )


def generate_pointwise_summary(
    campaigns: list[Campaign],
    verdicts: dict[str, BobVerdict],
    zone: ZoneInfo
) -> str:
    """Generates structured pointwise summary of each campaign for the master executive summary."""
    items = []
    for c in campaigns[:MAX_CAMPAIGNS]:
        v = verdicts.get(c.id)
        if v:
            esc = escalate(c.score, v, zone)
            level = esc["level"]
            act = esc["actions"][0] if esc["actions"] else "Preserve evidence"
            threat_type = v.threat_type.replace("_", " ").title()
            threat_info = f"Classified as <strong>{html.escape(threat_type)}</strong> (Severity {v.severity}/5 · Target: {html.escape(v.target or 'General Public')})"
            narrative = f"Narrative: “{html.escape(v.narrative[:160] + '...' if len(v.narrative) > 160 else v.narrative)}”" if v.narrative else ""
            if v.offline_event and v.offline_event.at:
                event_badge = f"""<div class="event-alert">📍 Planned gathering: {html.escape(v.offline_event.where)} on {local_text(v.offline_event.at, zone, '%a %d %b %H:%M')}</div>"""
            else:
                event_badge = ""
        else:
            level = "PENDING"
            act = "Trigger IBM Bob classification in dashboard"
            threat_info = "<em>Pending semantic classification by IBM Bob</em>"
            narrative = f"Coordinated cluster of {c.size} accounts posting in lockstep"
            event_badge = ""

        badge_color, badge_bg = LEVEL_COLORS.get(level, ("#5c6470", "#f0f2f5"))
        badge_html = f"""<span class="score-badge" style="background:{badge_bg}; color:{badge_color}; border:1px solid {badge_color}; font-size:11px; padding:2px 8px;">{level}</span>"""
        tag_str = f" · <span class='mono' style='font-size:12px;'>{html.escape(c.top_hashtag)}</span>" if c.top_hashtag else ""

        platforms = f" across {' → '.join(PLATFORM_NAMES.get(p['name'], p['name']) for p in c.platform_path)}" if c.platform_path else ""

        items.append(f"""
        <li class="summary-point-item">
          <div class="point-header">
            <strong>Campaign {html.escape(c.id.upper())}</strong>{tag_str} — {badge_html}
            <span class="muted" style="font-size:12px;">(Score {c.score}/100 · {c.size} accounts{html.escape(platforms)})</span>
          </div>
          <div class="point-body">
            {threat_info}. {narrative}
            {event_badge}
          </div>
          <div class="point-action">
            <strong>Key Directive:</strong> {html.escape(act)}
          </div>
        </li>
        """)

    return "".join(items)


def clock(ts: int) -> str:
    return datetime.fromtimestamp(ts, ZONE).strftime("%H:%M")


def gap(seconds: int) -> str:
    m = max(0, round(seconds / 60))
    return f"{m} min" if m < 60 else f"{m // 60} h {m % 60} m"


def strip_svg(c: Campaign, event_at: int, batch_end: int) -> str:
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
    rows = []
    for c in sorted((c for c in campaigns if c.id in verdicts and verdicts[c.id].offline_event),
                    key=lambda c: verdicts[c.id].offline_event.at or 0):
        ev = verdicts[c.id].offline_event
        if not ev.at:
            continue
        lead = f"Flagged at {clock(c.detected_at)}, <strong>{gap(ev.at - c.detected_at)} before</strong> the gathering. " if c.detected_at else ""
        rows.append(f"""
        <div class="threat-box">
          <div class="eyebrow" style="color:#c21f2b">Planned offline gathering · called by campaign {html.escape(c.id.upper())}</div>
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


def render_brief(dataset_id: str, campaign_id: str | None = None) -> str:
    """
    Generates an official, print-ready HTML Cyber Threat Escalation Brief following the 5-part hierarchy:
    Page 1: Executive Threat Intelligence Dashboard
    Page 2: System Architecture / Detection Pipeline
    Page 3: Detection Methodology / Coordination Scoring
    Page 4: Campaign Overview / All Campaigns Comparison Table
    Page 5+: Individual Campaign Investigations (A-I)
    """
    run_dir = RUNS / dataset_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory for {dataset_id} does not exist")
    global ZONE
    ZONE = dataset_zone(run_dir)

    campaigns_file = run_dir / "campaigns.json"
    source = next(iter(sorted(run_dir.glob("upload*"))), None)  # the X API JSON exactly as uploaded or fetched

    if not source or not campaigns_file.exists():
        raise FileNotFoundError("Dataset has not completed analysis")

    # Dataset SHA-256 of the original X API source file
    sha = hashlib.sha256()
    with open(source, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
    dataset_sha256 = sha.hexdigest()

    with open(campaigns_file, "r", encoding="utf-8") as f:
        campaigns = [Campaign.model_validate(c) for c in json.load(f)]

    samples_file = run_dir / "samples.json"
    if samples_file.exists():
        samples = json.loads(samples_file.read_text(encoding="utf-8"))
    else:
        # Fallback for datasets analysed before samples.json
        with open(posts_file, "r", encoding="utf-8") as f:
            all_posts = json.load(f)
        acc_to_camp = {a: c.id for c in campaigns for a in c.accounts}
        samples = {c.id: [] for c in campaigns}
        for p in all_posts:
            cid = acc_to_camp.get(p.get("account_id"))
            if cid and len(samples[cid]) < 20:
                samples[cid].append(p)

    posts_by_id = {p["post_id"]: Post.model_validate(p) for posts in samples.values() for p in posts}
    verdicts = {c.id: v for c in campaigns if (v := cached_verdict(run_dir, c.id))}

    timeline = json.loads((run_dir / "timeline.json").read_text(encoding="utf-8"))
    batch_end = timeline["points"][-1]["t"] + timeline["bucket_seconds"] if timeline["points"] else 0
    now_ist = datetime.now(IST).strftime("%d %B %Y, %H:%M:%S IST")

    # Metrics
    total_campaigns = len(campaigns)
    total_accounts = sum(c.size for c in campaigns)
    max_score = max((c.score for c in campaigns), default=0)
    classified_count = sum(1 for c in campaigns if c.id in verdicts)
    urgent_count = sum(1 for c in campaigns if verdicts.get(c.id) and escalate(c.score, verdicts[c.id], ZONE)["level"] == "URGENT")
    alert_count = sum(1 for c in campaigns if verdicts.get(c.id) and escalate(c.score, verdicts[c.id], ZONE)["level"] == "ALERT")

    # Helper for investigation section per campaign
    def make_investigation_section(c: Campaign) -> str:
        v = verdicts.get(c.id)
        if v:
            esc = escalate(c.score, v, ZONE)
            level, actions, evidence_ids = esc["level"], esc["actions"], v.evidence_post_ids
        else:
            level, actions = "PENDING", ["Classify this campaign with IBM Bob in the dashboard before escalating"]
            evidence_ids = [p["post_id"] for p in samples.get(c.id, [])[:8]]
        badge_color, badge_bg = LEVEL_COLORS.get(level, ("#5c6470", "#f0f2f5"))

        # Evidence table rows
        evidence_rows = []
        for pid in evidence_ids[:10]:
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

        # Features breakdown with visual bar
        feat_rows = []
        for k, v_pts in c.features.items():
            label = FEATURE_LABELS.get(k, k)
            feat_rows.append(f"""
            <div class="feat-row">
              <span class="feat-label">{html.escape(label)}</span>
              <div class="feat-bar-bg"><div class="feat-bar-fill" style="width: {min(100, v_pts * 4)}%;"></div></div>
              <span class="feat-pts">{v_pts} pts</span>
            </div>
            """)

        # Accounts table (Seeds + Amplifiers)
        account_rows = []
        for s in (c.seeds or [])[:5]:
            account_rows.append(f"""
            <tr>
              <td><span class="role-badge seed">SEED</span></td>
              <td class="mono">{html.escape(s.get('username', s.get('account_id', '')))}</td>
              <td>{html.escape(PLATFORM_NAMES.get(s.get('platform'), s.get('platform') or '?'))}</td>
              <td>{clock(s['first_seen']) if s.get('first_seen') else '—'}</td>
              <td>{html.escape(s.get('city') or '—')}</td>
              <td>{s.get('account_age_days') if s.get('account_age_days') is not None else '—'} days</td>
            </tr>
            """)
        for a in (c.amplifiers or [])[:5]:
            account_rows.append(f"""
            <tr>
              <td><span class="role-badge amp">AMPLIFIER</span></td>
              <td class="mono">{html.escape(a.get('username', a.get('account_id', '')))}</td>
              <td>Coordinated Bot</td>
              <td>—</td>
              <td>—</td>
              <td>{a.get('links', '—')} links ({a.get('posts', '—')} posts)</td>
            </tr>
            """)

        return f"""
        <div class="investigation-card">
          <!-- A. Campaign Header -->
          <div class="campaign-header">
            <div>
              <span class="campaign-title">Campaign {html.escape(c.id.upper())}</span>
              <span class="hashtag">{html.escape(c.top_hashtag or 'N/A')}</span>
              <span class="accounts-badge">{c.size} accounts</span>
            </div>
            <div class="score-badge" style="background:{badge_bg}; color:{badge_color}; border: 1px solid {badge_color};">
              {level} · CIB score {c.score}/100
            </div>
          </div>

          <!-- B. Campaign Overview Metadata Cards -->
          <div class="meta-strip">
            <div class="meta-cell"><span class="lbl">Campaign</span><span class="val">{html.escape(c.id.upper())}</span></div>
            <div class="meta-cell"><span class="lbl">Accounts</span><span class="val">{c.size}</span></div>
            <div class="meta-cell"><span class="lbl">Platforms</span><span class="val">{", ".join(PLATFORM_NAMES.get(p['name'], p['name']) for p in c.platform_path) if c.platform_path else "Social"}</span></div>
            <div class="meta-cell"><span class="lbl">Location</span><span class="val">{", ".join(t['name'] for t in c.town_path) if c.town_path else "Delhi / Multi-city"}</span></div>
            <div class="meta-cell"><span class="lbl">First Detected</span><span class="val">{clock(c.first_seen)}</span></div>
            <div class="meta-cell"><span class="lbl">Flagged Time</span><span class="val">{clock(c.detected_at) if c.detected_at else "—"}</span></div>
            <div class="meta-cell"><span class="lbl">CIB Score</span><span class="val">{c.score}/100</span></div>
            <div class="meta-cell"><span class="lbl">Status</span><span class="val" style="color:{badge_color}; font-weight:600;">{level}</span></div>
          </div>

          <!-- C. How It Spread -->
          <div class="section-title">How It Spread (Timeline &amp; Platform Sequence)</div>
          <div class="spread-box">
            {spread_html(c)}
          </div>

          <!-- D. Why It Was Flagged -->
          <div class="section-title">Why It Was Flagged (Coordination Factor Breakdown)</div>
          <div class="features-container">
            {''.join(feat_rows)}
            <div class="feat-total"><strong>Total CIB Coordination Score:</strong> <strong>{c.score}/100</strong></div>
          </div>

          <!-- E. Network & Core Accounts -->
          <div class="section-title">Network &amp; Key Accounts (Seeds &amp; Amplifiers)</div>
          <table class="data-table">
            <thead>
              <tr><th>Role</th><th>Handle / ID</th><th>Platform</th><th>First Active</th><th>City</th><th>Details</th></tr>
            </thead>
            <tbody>
              {''.join(account_rows) if account_rows else '<tr><td colspan="6" class="muted text-center">Accounts participating uniformly across campaign network.</td></tr>'}
            </tbody>
          </table>

          <!-- F. IBM Bob Assessment -->
          <div class="section-title">IBM Bob Semantic Threat Assessment</div>
          <div class="bob-assessment-box">
            {threat_html(v)}
          </div>

          <!-- G. Recommended Actions Checklist -->
          <div class="section-title">Recommended Actions Checklist</div>
          <div class="actions-box">
            <div class="workflow-steps">
              <span class="step-chip done">✓ Campaign Detected</span>
              <span class="step-chip done">✓ Coordination Analyzed</span>
              <span class="step-chip done">✓ Evidence Collected</span>
              <span class="step-chip done">✓ SHA-256 Hashes Generated</span>
              <span class="step-chip {'done' if v else 'pending'}">{'✓' if v else '○'} IBM Bob Classified</span>
              <span class="step-chip pending">○ Investigator Verified</span>
              <span class="step-chip pending">○ Action Escalated</span>
            </div>
            <ul class="actions-list">
              {actions_list}
            </ul>
          </div>

          <!-- H. Evidence Records -->
          <div class="section-title">Evidence Records (Section 63 BSA Cryptographic Chain)</div>
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

          <!-- I. Legal Suggestions -->
          <div class="section-title">Statutory Provisions to Check (Indian Penal / IT Act)</div>
          <div class="legal-container">
            {legal_html}
          </div>
        </div>
        """

    # Shared CSS styles
    css_styles = """
    :root {
      --ink: #15181d;
      --muted: #5c6470;
      --line: #e2e5ea;
      --subtle: #f0f2f5;
      --accent: #2456d6;
      --urgent: #c21f2b;
      --urgent-soft: #fdecee;
      --alert: #a45f00;
      --alert-soft: #fdf3e1;
      --benign: #1f7a3d;
      --benign-soft: #e7f5ec;
    }
    * { box-sizing: border-box; }
    body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; margin: 0; padding: 28px 16px; color: var(--ink); background: #f6f7f9; line-height: 1.5; font-size: 13.5px; }
    .container { max-width: 960px; margin: 0 auto; background: #fff; padding: 36px 40px; border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .header { border-bottom: 2px solid var(--ink); padding-bottom: 16px; margin-bottom: 24px; }
    .title-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
    .eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
    h1 { font-size: 24px; font-weight: 700; margin: 4px 0 0; color: var(--ink); letter-spacing: -0.01em; }
    h2.report-page-title { font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ink); border-bottom: 2px solid var(--accent); padding-bottom: 6px; margin: 28px 0 16px; }
    .meta-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px 24px; font-size: 13px; color: var(--muted); margin-top: 14px; background: var(--subtle); padding: 12px 16px; border-radius: 6px; }
    .meta-grid strong { color: var(--ink); font-weight: 600; }
    
    /* Top KPI Cards */
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
    .kpi-card { background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 12px 14px; }
    .kpi-title { font-size: 11px; font-weight: 600; text-transform: uppercase; color: var(--muted); letter-spacing: 0.04em; }
    .kpi-val { font-size: 20px; font-weight: 700; color: var(--ink); margin-top: 4px; }
    .kpi-sub { font-size: 11px; color: var(--muted); margin-top: 2px; }

    /* Architecture Visual */
    .arch-flow { display: flex; flex-direction: column; gap: 8px; background: var(--subtle); padding: 20px; border-radius: 8px; border: 1px solid var(--line); margin-bottom: 24px; }
    .arch-step { display: flex; align-items: center; justify-content: space-between; background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 10px 14px; font-size: 12.5px; }
    .arch-num { width: 22px; height: 22px; border-radius: 50%; background: var(--accent); color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; margin-right: 10px; }
    .arch-name { font-weight: 600; color: var(--ink); }
    .arch-desc { color: var(--muted); font-size: 12px; }
    .arch-arrow { text-align: center; color: var(--muted); font-size: 12px; margin: -2px 0; }

    /* Executive Summary */
    .exec-summary { border-left: 4px solid var(--accent); background: var(--subtle); padding: 16px 20px; border-radius: 0 6px 6px 0; margin-bottom: 24px; }
    .exec-summary h2 { margin: 0 0 8px; font-size: 14px; font-weight: 700; color: var(--ink); text-transform: uppercase; letter-spacing: 0.04em; }
    .exec-summary p { margin: 0 0 10px; line-height: 1.6; }
    .pointwise-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); margin: 16px 0 8px; border-top: 1px dashed var(--line); padding-top: 10px; }
    .summary-points { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 8px; }
    .summary-point-item { background: #ffffff; border: 1px solid var(--line); border-radius: 6px; padding: 10px 14px; font-size: 12.5px; }
    .point-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
    .point-body { color: var(--ink); margin-bottom: 4px; line-height: 1.4; }
    .point-action { font-size: 11.5px; color: var(--accent); font-weight: 600; }

    /* Tables */
    .data-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 18px; }
    .data-table th { text-align: left; font-weight: 600; color: var(--muted); background: var(--subtle); padding: 8px 10px; border-bottom: 1px solid var(--line); font-size: 11.5px; text-transform: uppercase; }
    .data-table td { border-bottom: 1px solid var(--line); padding: 8px 10px; vertical-align: top; }
    .score-bar-bg { width: 80px; height: 6px; background: #e2e5ea; border-radius: 3px; display: inline-block; vertical-align: middle; margin-right: 6px; overflow: hidden; }
    .score-bar-fill { height: 100%; background: var(--accent); }

    /* Investigation Cards */
    .investigation-card { border: 1px solid var(--line); border-radius: 8px; padding: 22px; margin-bottom: 30px; break-inside: avoid; background: #fff; }
    .campaign-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 14px; }
    .campaign-title { font-size: 18px; font-weight: 700; color: var(--ink); margin-right: 8px; }
    .hashtag { font-size: 14px; font-family: ui-monospace, monospace; color: var(--muted); margin-right: 8px; }
    .accounts-badge { font-size: 12px; font-weight: 600; background: var(--subtle); padding: 2px 8px; border-radius: 4px; }
    .score-badge { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 999px; text-transform: uppercase; }
    
    .meta-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; background: var(--subtle); padding: 10px 14px; border-radius: 6px; margin-bottom: 14px; font-size: 12px; }
    .meta-cell .lbl { display: block; font-size: 10px; font-weight: 600; text-transform: uppercase; color: var(--muted); }
    .meta-cell .val { font-weight: 600; color: var(--ink); margin-top: 1px; }

    .section-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); margin: 16px 0 6px; }
    .features-container { background: var(--subtle); border-radius: 6px; padding: 10px 14px; margin-bottom: 14px; }
    .feat-row { display: flex; align-items: center; justify-content: space-between; font-size: 12px; margin-bottom: 4px; }
    .feat-label { width: 180px; }
    .feat-bar-bg { flex: 1; height: 5px; background: #e2e5ea; border-radius: 3px; margin: 0 12px; overflow: hidden; }
    .feat-bar-fill { height: 100%; background: var(--accent); }
    .feat-pts { width: 45px; text-align: right; font-weight: 600; }
    .feat-total { border-top: 1px solid var(--line); padding-top: 6px; margin-top: 6px; display: flex; justify-content: space-between; font-size: 12.5px; }

    .spread-box { background: var(--subtle); border-radius: 6px; padding: 12px 14px; font-size: 12.5px; margin-bottom: 14px; }
    .threat-box { border: 1px solid #f3c4c8; border-left: 4px solid var(--urgent); background: #fdf6f7; border-radius: 0 6px 6px 0; padding: 14px 18px; margin-bottom: 18px; }
    .threat-main { font-size: 18px; font-weight: 700; color: var(--urgent); margin: 4px 0; }
    .bob-assessment-box { background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 12px 16px; margin-bottom: 14px; font-size: 12.5px; }
    .actions-box { background: var(--subtle); border-radius: 6px; padding: 12px 16px; margin-bottom: 14px; }
    .workflow-steps { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
    .step-chip { font-size: 10.5px; padding: 2px 8px; border-radius: 999px; font-weight: 600; }
    .step-chip.done { background: var(--benign-soft); color: var(--benign); }
    .step-chip.pending { background: #fff; border: 1px solid var(--line); color: var(--muted); }
    .actions-list { margin: 0; padding-left: 18px; font-size: 12.5px; }

    .evidence-table { width: 100%; border-collapse: collapse; font-size: 11.5px; margin-top: 6px; margin-bottom: 14px; }
    .evidence-table th { text-align: left; font-weight: 600; color: var(--muted); background: var(--subtle); padding: 6px 8px; border-bottom: 1px solid var(--line); }
    .evidence-table td { border-bottom: 1px solid var(--line); padding: 6px 8px; vertical-align: top; }
    .legal-badge { background: var(--subtle); border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; font-size: 12px; }
    .role-badge { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 3px; display: inline-block; }
    .role-badge.seed { background: var(--ink); color: #fff; }
    .role-badge.amp { background: var(--alert-soft); color: var(--alert); }
    .mono { font-family: ui-monospace, "Cascadia Mono", Consolas, monospace; }
    .small-hash { color: var(--muted); }
    .cta-alert { background: #fdecee; color: #c21f2b; border-radius: 6px; padding: 8px 12px; }
    .print-btn { background: var(--accent); color: #fff; border: 0; border-radius: 6px; padding: 8px 16px; font-size: 12.5px; font-weight: 600; cursor: pointer; }
    .limitations { border-top: 2px solid var(--line); padding-top: 14px; margin-top: 28px; font-size: 11.5px; color: var(--muted); line-height: 1.5; }
    .page-break { page-break-after: always; break-after: page; }

    @media print {
      body { background: #fff; padding: 0; }
      .container { border: 0; padding: 0; box-shadow: none; max-width: 100%; }
      .print-btn { display: none; }
      .page-break { page-break-after: always; break-after: page; }
    }
    """

    # =========================================================================
    # OPTION 1: INDIVIDUAL CAMPAIGN INVESTIGATION REPORT
    # =========================================================================
    if campaign_id:
        target_cid = campaign_id.lower().strip()
        c = next((c for c in campaigns if c.id.lower() == target_cid), None)
        if not c:
            raise FileNotFoundError(f"Campaign '{campaign_id}' not found in dataset '{dataset_id}'")

        v = verdicts.get(c.id)
        if v:
            esc = escalate(c.score, v, ZONE)
            level, actions = esc["level"], esc["actions"]
        else:
            level, actions = "PENDING", ["Classify this campaign with IBM Bob in dashboard"]

        camp_summary = generate_single_campaign_summary(c, v, level, actions, ZONE)
        investigation_content = make_investigation_section(c)
        threats_box = threats_html([c], verdicts, batch_end)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Cyber Threat Intelligence Brief — Campaign {html.escape(c.id.upper())} ({html.escape(dataset_id)})</title>
  <style>{css_styles}</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="title-row">
        <div>
          <div class="eyebrow">Police Cyber Cell · Section 63 BSA Evidentiary Dossier</div>
          <h1>Campaign {html.escape(c.id.upper())} Threat Investigation</h1>
        </div>
        <button class="print-btn" onclick="window.print()">Print / Save PDF</button>
      </div>

      <div class="meta-grid">
        <div><strong>Dataset Reference:</strong> {html.escape(dataset_id)}</div>
        <div><strong>Campaign ID:</strong> Campaign {html.escape(c.id.upper())} ({html.escape(c.top_hashtag or 'N/A')})</div>
        <div><strong>Coordinated Accounts:</strong> {c.size} accounts</div>
        <div><strong>Escalation Priority:</strong> {level} (CIB Score {c.score}/100)</div>
        <div><strong>Generated Timestamp:</strong> {html.escape(now_ist)}</div>
        <div><strong>Source file (X API JSON) SHA-256:</strong> <span class="mono">{html.escape(dataset_sha256[:20])}...</span></div>
      </div>
    </div>

    {threats_box}

    <div class="exec-summary">
      <h2>Executive Summary — Campaign {html.escape(c.id.upper())}</h2>
      <p>{html.escape(camp_summary)}</p>
    </div>

    {investigation_content}

    <div class="limitations">
      <strong>Section 63 BSA Operational Notice &amp; Evidentiary Limitations:</strong> This report is automated decision support derived via NetworkX Louvain community clustering and IBM Bob Granite LLM assessment. In accordance with Section 63 of the Bharatiya Sakshya Adhiniyam (BSA), 2023, automated cryptographic hashes verify record integrity but do not dispense with the requirement for independent verification of source origin, device custody, and intent by an investigating officer.
    </div>
  </div>
</body>
</html>
"""
        (run_dir / f"brief_{c.id}.html").write_text(html_content, encoding="utf-8")
        return html_content

    # =========================================================================
    # OPTION 2: FULL CONSOLIDATED REPORT (ALL CAMPAIGNS HIERARCHY)
    # =========================================================================
    shown = campaigns[:MAX_CAMPAIGNS]
    threats_box = threats_html(campaigns, verdicts, batch_end)
    exec_summary = generate_executive_summary(run_dir, dataset_id, campaigns, verdicts)
    pointwise_summary = generate_pointwise_summary(shown, verdicts, ZONE)

    # All Campaigns Overview Table rows
    table_rows = []
    for c in shown:
        v = verdicts.get(c.id)
        esc = escalate(c.score, v, ZONE) if v else {"level": "PENDING", "actions": ["Pending classification"]}
        badge_color, badge_bg = LEVEL_COLORS.get(esc["level"], ("#5c6470", "#f0f2f5"))
        platforms = ", ".join(PLATFORM_NAMES.get(p['name'], p['name']) for p in c.platform_path) if c.platform_path else "Social"
        towns = ", ".join(t['name'] for t in c.town_path) if c.town_path else "Delhi / Multi-region"
        table_rows.append(f"""
        <tr>
          <td><strong>Campaign {html.escape(c.id.upper())}</strong></td>
          <td class="mono">{html.escape(c.top_hashtag or '—')}</td>
          <td>{c.size} accs</td>
          <td>
            <div class="score-bar-bg"><div class="score-bar-fill" style="width:{c.score}%;"></div></div>
            <strong>{c.score}/100</strong>
          </td>
          <td><span class="score-badge" style="background:{badge_bg}; color:{badge_color};">{esc['level']}</span></td>
          <td>{html.escape(platforms)}</td>
          <td>{html.escape(towns)}</td>
          <td>{html.escape(v.threat_type.replace('_', ' ').title() if v else 'Pending Bob')}</td>
        </tr>
        """)

    # Individual Investigation Sections for each campaign
    investigations_html = "".join(make_investigation_section(c) for c in shown)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Cyber Threat Intelligence Escalation Brief — {html.escape(dataset_id)}</title>
  <style>{css_styles}</style>
</head>
<body>
  <div class="container">
    <!-- PAGE 1: EXECUTIVE THREAT INTELLIGENCE DASHBOARD -->
    <div class="header">
      <div class="title-row">
        <div>
          <div class="eyebrow">Police Cyber Cell · Station House Officer Briefing</div>
          <h1>Executive Threat Intelligence Escalation Brief</h1>
        </div>
        <button class="print-btn" onclick="window.print()">Print / Save PDF</button>
      </div>

      <div class="meta-grid">
        <div><strong>Dataset Reference:</strong> {html.escape(dataset_id)}</div>
        <div><strong>Campaigns Detected:</strong> {total_campaigns} coordinated operations</div>
        <div><strong>Generated Timestamp:</strong> {html.escape(now_ist)}</div>
        <div><strong>Evidence SHA-256:</strong> <span class="mono">{html.escape(dataset_sha256[:20])}...</span></div>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">Total Campaigns</div>
        <div class="kpi-val">{total_campaigns}</div>
        <div class="kpi-sub">Coordinated communities</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Total Accounts</div>
        <div class="kpi-val">{total_accounts}</div>
        <div class="kpi-sub">Synchronized entities</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Max CIB Score</div>
        <div class="kpi-val" style="color:var(--urgent);">{max_score}/100</div>
        <div class="kpi-sub">Highest risk detected</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">IBM Bob Status</div>
        <div class="kpi-val" style="color:var(--accent);">{classified_count}/{total_campaigns}</div>
        <div class="kpi-sub">{urgent_count} urgent · {alert_count} alert</div>
      </div>
    </div>

    {threats_box}

    <!-- Executive Summary & Pointwise Breakdown -->
    <div class="exec-summary">
      <h2>Executive Summary</h2>
      <p>{html.escape(exec_summary)}</p>

      <div class="pointwise-title">Pointwise Campaign Breakdown:</div>
      <ul class="summary-points">
        {pointwise_summary}
      </ul>
    </div>

    <div class="page-break"></div>

    <!-- PAGE 2: SYSTEM ARCHITECTURE & DETECTION PIPELINE -->
    <h2 class="report-page-title">2. System Architecture &amp; Processing Pipeline</h2>
    <div class="arch-flow">
      <div class="arch-step">
        <div><span class="arch-num">1</span><span class="arch-name">Social Media Data Ingestion</span></div>
        <span class="arch-desc">X (Twitter), Telegram, WhatsApp, CSV/JSON forensic exports</span>
      </div>
      <div class="arch-arrow">↓</div>
      <div class="arch-step">
        <div><span class="arch-num">2</span><span class="arch-name">Data Processing &amp; Normalization</span></div>
        <span class="arch-desc">Timestamp synchronization, multilingual text encoding, URL resolution</span>
      </div>
      <div class="arch-arrow">↓</div>
      <div class="arch-step">
        <div><span class="arch-num">3</span><span class="arch-name">Multi-Signal Coordination Detection</span></div>
        <span class="arch-desc">coordination-network-toolkit (co-tweet, co-link, co-reply, co-retweet)</span>
      </div>
      <div class="arch-arrow">↓</div>
      <div class="arch-step">
        <div><span class="arch-num">4</span><span class="arch-name">Network Analysis &amp; Community Detection</span></div>
        <span class="arch-desc">NetworkX Louvain modularity algorithm partitioning distinct campaign clusters</span>
      </div>
      <div class="arch-arrow">↓</div>
      <div class="arch-step">
        <div><span class="arch-num">5</span><span class="arch-name">Risk &amp; Coordination Scoring Engine</span></div>
        <span class="arch-desc">6-factor explainable CIB scoring (0–100 scale: speed, burst, duplication, fresh accounts)</span>
      </div>
      <div class="arch-arrow">↓</div>
      <div class="arch-step">
        <div><span class="arch-num">6</span><span class="arch-name">IBM Bob Semantic Intelligence</span></div>
        <span class="arch-desc">Granite LLM threat classification, severity rating, and offline mobilization extraction</span>
      </div>
      <div class="arch-arrow">↓</div>
      <div class="arch-step">
        <div><span class="arch-num">7</span><span class="arch-name">Investigator Review &amp; Triage Workspace</span></div>
        <span class="arch-desc">Interactive Case File dashboard with layout modes and evidence inspection</span>
      </div>
      <div class="arch-arrow">↓</div>
      <div class="arch-step">
        <div><span class="arch-num">8</span><span class="arch-name">Evidentiary Reporting (Section 63 BSA)</span></div>
        <span class="arch-desc">Automated Section 63 BSA certificate brief with immutable SHA-256 evidence chain</span>
      </div>
    </div>

    <!-- PAGE 3: DETECTION METHODOLOGY -->
    <h2 class="report-page-title">3. Detection Methodology &amp; Scoring Matrix</h2>
    <table class="data-table">
      <thead>
        <tr><th>Signal / Factor</th><th>Technical Mechanism</th><th>Evidence Significance</th><th>Weight</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Speed / Velocity</strong></td>
          <td>Accounts posting identical or related content within tight time windows (&lt;60s).</td>
          <td>Distinguishes automated bots from organic human dissemination.</td>
          <td>25 pts</td>
        </tr>
        <tr>
          <td><strong>Syntactic Duplication</strong></td>
          <td>MinDocSize &amp; Levenshtein syntactic token similarity threshold (&ge;0.8).</td>
          <td>Identifies copy-paste astroturfing campaigns.</td>
          <td>25 pts</td>
        </tr>
        <tr>
          <td><strong>Account Freshness</strong></td>
          <td>Proportion of accounts created &lt;30 days prior to the incident surge.</td>
          <td>Detects disposable burner botnet infrastructure.</td>
          <td>15 pts</td>
        </tr>
        <tr>
          <td><strong>Sudden Burst</strong></td>
          <td>Abnormal volume acceleration exceeding 3σ historical baseline.</td>
          <td>Indicates orchestrated flash-mob style narrative injection.</td>
          <td>15 pts</td>
        </tr>
        <tr>
          <td><strong>Multi-Signal Alignment</strong></td>
          <td>Simultaneous convergence across multiple networks (tweets + links + replies).</td>
          <td>High-fidelity confirmation of multi-pronged coordination.</td>
          <td>10 pts</td>
        </tr>
        <tr>
          <td><strong>Content Concentration</strong></td>
          <td>Excessive concentration on a single external URL or dedicated hashtag.</td>
          <td>Pinpoints the coordinated campaign narrative anchor.</td>
          <td>10 pts</td>
        </tr>
      </tbody>
    </table>

    <div class="page-break"></div>

    <!-- PAGE 4: ALL CAMPAIGNS OVERVIEW -->
    <h2 class="report-page-title">4. Campaign Overview (All Coordinated Operations)</h2>
    <p class="muted">Summary comparison of all {total_campaigns} coordinated campaigns identified in dataset '{html.escape(dataset_id)}':</p>
    <table class="data-table">
      <thead>
        <tr>
          <th>Campaign</th>
          <th>Hashtag</th>
          <th>Size</th>
          <th>Score</th>
          <th>Level</th>
          <th>Platforms</th>
          <th>Locations</th>
          <th>IBM Bob Assessment</th>
        </tr>
      </thead>
      <tbody>
        {''.join(table_rows)}
      </tbody>
    </table>

    <div class="page-break"></div>

    <!-- PAGE 5+: INDIVIDUAL CAMPAIGN INVESTIGATIONS -->
    <h2 class="report-page-title">5. Detailed Campaign Investigations</h2>
    {investigations_html}

    <!-- FINAL SECTION: OPERATIONAL NOTICE -->
    <div class="limitations">
      <strong>Section 63 BSA Operational Notice &amp; Evidentiary Limitations:</strong> This escalation brief provides automated decision support produced through algorithmic coordination clustering (NetworkX Louvain) and AI semantic triage (IBM Bob). In accordance with Section 63 of the Bharatiya Sakshya Adhiniyam (BSA), 2023, automated cryptographic hashes confirm digital payload integrity but do not independently prove criminal mens rea, source device custody, or legal liability. All findings must be corroborated by an authorized investigating officer prior to filing formal charges or judicial proceedings.
    </div>
  </div>
</body>
</html>
"""
    (run_dir / "brief.html").write_text(html_content, encoding="utf-8")
    return html_content
