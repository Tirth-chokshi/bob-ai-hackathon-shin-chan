import React, { useEffect, useRef, useState } from 'react'
import { AlertTriangle, Clock, MapPin, MousePointerClick, Phone } from 'lucide-react'
import { api } from '../api'
import { Badge, Button, Label, LevelBadge, ScoreBar, Spinner } from '../ui'
import { LangChips, PlatformChip, PlatformChips } from './Chips'
import { SpreadPath } from './SpreadPath'
import { campaignColor, FEATURES, SIGNALS, THREATS, fmt, fmtClock, fmtDay, fmtGap, fmtRange, fmtWhen, langLabel, platformLabel } from '../labels'

// Campaign detail, top to bottom: identity → called gathering → how it spread → who started it →
// why flagged → IBM Bob assessment → posts
// Sections whose data a dataset doesn't have (platforms, towns, account ages) are left out or reduced to one line
export function CampaignPanel({ datasetId, campaignId, bobConfigured, onAssessed, onFilter = () => {} }) {
  const [campaign, setCampaign] = useState(null)
  const [result, setResult] = useState(null) // { verdict, escalation, cached, cost }
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState(null)
  const current = useRef(campaignId)
  current.current = campaignId

  useEffect(() => {
    setCampaign(null)
    setResult(null)
    setError(null)
    if (!campaignId) return
    let cancelled = false
    api.campaign(datasetId, campaignId)
      .then((c) => !cancelled && setCampaign(c))
      .catch((e) => !cancelled && setError(e.message))
    api.verdict(datasetId, campaignId) // cached only; 404 = not assessed yet
      .then((v) => !cancelled && setResult(v))
      .catch(() => {})
    return () => { cancelled = true }
  }, [datasetId, campaignId])

  const ask = async () => {
    const cid = campaignId
    setAsking(true)
    setError(null)
    try {
      const r = await api.classify(datasetId, cid)
      onAssessed(cid, {
        threat_type: r.verdict.threat_type, severity: r.verdict.severity,
        level: r.escalation.level, offline_event: r.verdict.offline_event,
      })
      if (current.current === cid) setResult(r)
    } catch (e) {
      if (current.current === cid) setError(e.message)
    } finally {
      setAsking(false)
    }
  }

  if (!campaignId) {
    return (
      <div className="bg-surface border border-line rounded-lg p-6 text-center text-sm text-muted">
        <MousePointerClick className="w-6 h-6 mx-auto text-faint mb-2" aria-hidden />
        Select a campaign to see how it spread, why it was flagged and IBM Bob's assessment.
      </div>
    )
  }
  if (!campaign) {
    return (
      <div className="bg-surface border border-line rounded-lg p-6 text-sm text-muted flex items-center justify-center gap-2">
        {error ? <span className="text-urgent">{error}</span> : <><Spinner /> Loading campaign…</>}
      </div>
    )
  }

  const color = campaignColor(campaign.id)
  const evidence = new Set(result?.verdict.evidence_post_ids ?? [])
  const event = result?.verdict.offline_event

  const hasSeeds = campaign.seeds?.length > 0
  const hasPlatformPath = campaign.platform_path?.length > 1   // one platform is not a path; the chip says which
  const hasTownPath = campaign.town_path?.length > 0
  const span = campaign.last_seen - campaign.first_seen
  const when = (t) => fmtWhen(t, span)
  const reach = campaign.reach ?? {}

  return (
    <article className="bg-surface border border-line rounded-lg divide-y divide-line">
      {/* 1. Identity */}
      <header className="p-4 space-y-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-3 h-3 rounded-full shrink-0" style={{ background: color }} />
          <h2 className="text-base font-semibold">Campaign {campaign.id.toUpperCase()}</h2>
          {campaign.top_hashtag && (
            <button onClick={() => onFilter({ hashtag: campaign.top_hashtag })} title="All posts with this hashtag"
              className="text-sm text-muted truncate cursor-pointer hover:text-accent hover:underline">{campaign.top_hashtag}</button>
          )}
          {result && <span className="ml-auto"><LevelBadge level={result.escalation.level} /></span>}
        </div>
        <p className="text-xs text-muted font-mono">
          {fmt(campaign.size)} accounts · {fmt(campaign.post_count)} posts · {fmtRange(campaign.first_seen, campaign.last_seen)}
        </p>
        <div className="flex flex-wrap gap-2">
          {campaign.platform_path?.length > 0 && <PlatformChips names={campaign.platform_path.map((p) => p.name)} />}
          {campaign.languages && <LangChips languages={campaign.languages} />}
        </div>
      </header>

      {/* 2. Called gathering (from IBM Bob, checked in code) */}
      {event && (
        <section className="p-4">
          <div className="rounded-md bg-urgent-soft text-urgent p-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide">
              <AlertTriangle className="w-3.5 h-3.5" aria-hidden /> Call to gather
            </div>
            <div className="mt-1.5 flex flex-wrap gap-x-5 gap-y-1 text-sm">
              <span className="flex items-center gap-1 font-semibold"><MapPin className="w-4 h-4" aria-hidden />{event.where}</span>
              <span className="flex items-center gap-1 font-semibold font-mono"><Clock className="w-4 h-4" aria-hidden />{fmtDay(event.at)}, {fmtClock(event.at)}</span>
            </div>
            <p className="text-xs mt-1 opacity-90">{event.what} · posts say "{event.where_quote}"</p>
          </div>
        </section>
      )}

      {/* 2b. Offline call to action without a specific place and time */}
      {!event && result?.verdict.offline_call_to_action && (
        <section className="p-4">
          <div className="rounded-md bg-urgent-soft text-urgent p-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide">
              <AlertTriangle className="w-3.5 h-3.5" aria-hidden /> Offline call to action detected
            </div>
            <p className="text-sm mt-1">
              This campaign contains posts calling for real-world physical action. Verify posts and consider preventive measures.
            </p>
          </div>
        </section>
      )}

      {/* 3. How it spread: platform and town paths when the data has them, and always the timing */}
      <section className="p-4 space-y-3">
        <Label>{hasPlatformPath || hasTownPath ? 'How it spread' : 'How fast it moved'}</Label>
        {hasPlatformPath && <SpreadPath path={campaign.platform_path} kind="platform" span={span} />}
        {hasTownPath && <SpreadPath path={campaign.town_path} kind="town" span={span} />}
        <ul className="text-xs text-muted space-y-0.5">
          {reach.to_10_accounts_min != null && (reach.to_90pct_min === reach.to_10_accounts_min ? (
            <li>All but a few of its <strong className="text-ink">{fmt(campaign.size)} accounts</strong> posted within {fmtGap(reach.to_90pct_min * 60)} of the first post</li>
          ) : (
            <li><strong className="text-ink">10 accounts</strong> posted within {fmtGap(reach.to_10_accounts_min * 60)} of the first post
              {reach.to_90pct_min != null && <>, and 90% of its {fmt(campaign.size)} accounts within {fmtGap(reach.to_90pct_min * 60)}</>}</li>
          ))}
          {campaign.new_account_share != null && (
            <li><strong className={campaign.new_account_share >= 0.5 ? 'text-urgent' : 'text-ink'}>{Math.round(campaign.new_account_share * 100)}%</strong> of its accounts were under 30 days old when they posted</li>
          )}
          {campaign.detected_at && (
            <li>Flagged at <strong className="text-benign font-mono">{when(campaign.detected_at)}</strong>, {fmtGap(campaign.detected_at - campaign.first_seen)} after its first post
              {!hasPlatformPath && !hasTownPath && campaign.platform_path?.length === 1 && <> · all on {platformLabel(campaign.platform_path[0].name).label}</>}</li>
          )}
          {!hasTownPath && <li className="text-faint">No town or location field in this dataset, so there is no map.</li>}
        </ul>
      </section>

      {/* 4. Who started it, who amplified it */}
      {hasSeeds && (
        <section className="p-4 space-y-3">
          <Label>Who started it</Label>
          <ul className="space-y-2">
            {campaign.seeds.map((s) => (
              <li key={s.account_id} className="flex gap-2.5">
                <span className="w-8 h-8 rounded-full shrink-0 grid place-items-center text-sm font-semibold text-white" style={{ background: color }}>
                  {s.username.startsWith('+') ? <Phone className="w-4 h-4" aria-label="Phone number" /> : s.username.replace(/^@/, '').charAt(0).toUpperCase()}
                </span>
                <div className="min-w-0 text-xs">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <button onClick={() => onFilter({ account: s.account_id })} className="font-medium text-sm truncate cursor-pointer hover:text-accent hover:underline">{s.username}</button>
                    {s.platform && <PlatformChip platform={s.platform} />}
                    <span className="font-mono text-muted">{when(s.first_seen)}</span>
                    {s.account_age_days != null && (
                      <span className={s.account_age_days < 30 ? 'text-urgent' : 'text-muted'}>· account {s.account_age_days} days old</span>
                    )}
                  </div>
                  <p className="text-muted line-clamp-2">{s.text}</p>
                </div>
              </li>
            ))}
          </ul>
          {campaign.amplifiers?.length > 0 && (
            <div>
              <div className="text-xs text-muted mb-1.5">Most connected accounts (amplifiers)</div>
              <ul className="space-y-1">
                {campaign.amplifiers.map((a) => (
                  <li key={a.account_id} className="flex items-center gap-2 text-xs">
                    <button onClick={() => onFilter({ account: a.account_id })} title={a.username}
                      className="w-32 truncate text-left font-medium cursor-pointer hover:text-accent hover:underline">{a.username}</button>
                    <ScoreBar value={a.links} max={campaign.amplifiers[0].links || 1} color={color} />
                    <span className="w-20 shrink-0 text-right font-mono text-muted whitespace-nowrap">{fmt(a.posts)} posts</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {/* 4b. Account list — for uploaded datasets without seeds */}
      {!hasSeeds && campaign.accounts?.length > 0 && (
        <section className="p-4 space-y-3">
          <Label>Accounts ({fmt(campaign.accounts.length)} total)</Label>
          <div className="flex flex-wrap gap-1.5">
            {campaign.accounts.slice(0, 20).map((acc) => (
              <button key={acc} onClick={() => onFilter({ account: acc })}
                className="inline-flex items-center h-6 px-2 rounded-md bg-subtle text-xs font-mono text-muted cursor-pointer hover:text-accent">
                @{acc}
              </button>
            ))}
            {campaign.accounts.length > 20 && (
              <span className="inline-flex items-center h-6 px-2 text-xs text-faint">
                +{campaign.accounts.length - 20} more
              </span>
            )}
          </div>
        </section>
      )}

      {/* 5. Why flagged */}
      <section className="p-4 space-y-3">
        <div className="flex items-baseline justify-between">
          <Label>Why it was flagged</Label>
          <span className="font-mono text-sm"><strong className="text-lg">{campaign.score}</strong> / 100</span>
        </div>
        <ul className="space-y-2.5">
          {Object.entries(campaign.features).map(([key, points]) => {
            const f = FEATURES[key] ?? { label: key, max: 25 }
            return (
              <li key={key}>
                <div className="flex justify-between text-xs mb-1">
                  <span>{f.label}</span>
                  <span className="font-mono text-muted">{points}/{f.max}</span>
                </div>
                <ScoreBar value={points} max={f.max} color={color} />
              </li>
            )
          })}
        </ul>
        <div className="flex flex-wrap gap-1.5 pt-1">
          {campaign.signals.map((s) => <Badge key={s}>{SIGNALS[s] ?? s}</Badge>)}
        </div>
        {campaign.median_account_age_days != null && (
          <p className="text-xs text-muted">
            Median account age: <strong className={campaign.median_account_age_days < 30 ? 'text-urgent' : 'text-ink'}>
              {campaign.median_account_age_days} days
            </strong>
          </p>
        )}
      </section>

      {/* 6. IBM Bob assessment */}
      <section className="p-4 space-y-3">
        <Label>IBM Bob assessment</Label>
        {asking ? (
          <p className="flex items-center gap-2 text-sm text-muted">
            <Spinner className="w-4 h-4 text-accent" /> IBM Bob is reading the campaign analysis and 20 posts across it (about 20 seconds).
          </p>
        ) : result ? (
          <Assessment result={result} />
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-muted">
              Not assessed yet. IBM Bob reads the coordination analysis and 20 posts from across the campaign, in any
              language, and returns the threat type, target, severity, any call to gather, legal sections to check and
              the posts it relied on.
            </p>
            <Button variant="primary" onClick={ask} disabled={!bobConfigured}>Ask IBM Bob</Button>
            {!bobConfigured && (
              <p className="text-xs text-muted">Live assessments need BOB_API_KEY in src/.env and IBM Bob Shell (`bob`) on the backend's PATH.</p>
            )}
          </div>
        )}
        {error && <p className="text-sm text-urgent">{error}</p>}
      </section>

      {/* 7. Posts */}
      <section className="p-4">
        <div className="flex items-baseline justify-between gap-2 mb-3">
          <Label>Posts from across the campaign</Label>
          <button onClick={() => onFilter({ campaign: campaign.id })} className="text-xs text-accent cursor-pointer hover:underline whitespace-nowrap">
            All {fmt(campaign.post_count)} posts →
          </button>
        </div>
        <ol className="space-y-2">
          {campaign.sample_posts.map((p) => (
            <li key={p.post_id} className={`rounded-md border p-3 text-sm ${evidence.has(p.post_id) ? 'border-accent/50 bg-subtle' : 'border-line'}`}>
              <div className="flex items-center gap-1.5 text-xs text-muted mb-1">
                {p.platform && <PlatformChip platform={p.platform} />}
                <button onClick={() => onFilter({ account: p.account_id })} className="truncate font-mono cursor-pointer hover:text-accent hover:underline">
                  {p.platform === 'whatsapp' ? p.username : `@${(p.username || p.account_id).replace(/^@/, '')}`}
                </button>
                {p.city && <span className="shrink-0">· {p.city}</span>}
                <span className="ml-auto shrink-0 font-mono">{when(p.created_at)}</span>
              </div>
              <p className="break-words">{p.text}</p>
              <div className="flex items-center justify-between mt-1.5 text-xs font-mono text-faint">
                <span className="truncate">{p.post_id}{p.language ? ` · ${langLabel(p.language)}` : ''}</span>
                {evidence.has(p.post_id) && <span className="text-accent font-sans shrink-0">Cited by IBM Bob</span>}
              </div>
            </li>
          ))}
        </ol>
      </section>
    </article>
  )
}

function Assessment({ result }) {
  const { verdict, escalation, cached, cost } = result
  return (
    <div className="space-y-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <LevelBadge level={escalation.level} />
        <span className="font-medium">{THREATS[verdict.threat_type] ?? verdict.threat_type}</span>
        <span className="text-muted">· severity {verdict.severity} of 5</span>
        <span className="ml-auto text-xs text-faint">{cached ? 'Saved result' : `Cost ${cost.toFixed(3)} Bobcoins`}</span>
      </div>

      <dl className="space-y-2">
        <div><dt className="text-xs text-muted">Target</dt><dd>{verdict.target}</dd></div>
        <div><dt className="text-xs text-muted">Narrative</dt><dd>{verdict.narrative}</dd></div>
      </dl>

      <div>
        <div className="text-xs text-muted mb-1">Recommended actions</div>
        <ul className="list-disc pl-5 space-y-0.5">
          {escalation.actions.map((a) => <li key={a}>{a}</li>)}
        </ul>
      </div>

      {verdict.legal_suggestions.length > 0 && (
        <div>
          <div className="text-xs text-muted mb-1">Legal sections to check <span className="text-alert">(verify with a legal officer)</span></div>
          <ul className="space-y-1.5">
            {verdict.legal_suggestions.map((s) => (
              <li key={s.id} className="rounded-md bg-subtle px-3 py-2">
                <div className="font-medium">{s.law} <span className="text-muted font-normal">{s.ipc && s.ipc !== '—' && `(was ${s.ipc}) · `}{s.title}</span></div>
                <div className="text-muted text-xs mt-0.5">{s.why}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
