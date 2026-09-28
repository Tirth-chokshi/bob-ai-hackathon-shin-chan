import React, { useEffect, useState } from 'react'
import {
  ArrowRight,
  Bot,
  Clock,
  Compass,
  ExternalLink,
  Flame,
  Globe,
  Layers,
  MapPin,
  MessageSquare,
  Radio,
  Repeat,
  Share2,
  ShieldAlert,
  Sparkles,
  Users,
  Zap,
} from 'lucide-react'
import { api } from '../api'
import { Badge, Button, LevelBadge, ScoreBar, Spinner } from '../ui'
import { SpreadPath } from './SpreadPath'
import {
  campaignColor,
  FEATURES,
  fmt,
  fmtClock,
  fmtDay,
  fmtWhen,
  langLabel,
  platformLabel,
  SIGNALS,
  THREATS,
} from '../labels'

const SIGNAL_DESC = {
  co_tweet: 'Identical message posted across multiple accounts within seconds',
  co_similar_tweet: 'Near-identical text modified to evade simple duplicate filters',
  co_link: 'Coordinated dissemination of the same external link / URL',
  co_reply: 'Synchronized pile-on replying to the same target post',
  co_retweet: 'Coordinated artificial retweet velocity boosting visibility',
}

export function PropagationFlow({
  datasetId,
  campaigns,
  selectedId,
  onSelect,
  onOpenPosts,
  onSwitchToGraph,
}) {
  const [activeId, setActiveId] = useState(selectedId || campaigns[0]?.id || null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (selectedId && selectedId !== activeId) {
      setActiveId(selectedId)
    }
  }, [selectedId])

  useEffect(() => {
    if (!activeId) return
    let cancelled = false
    setLoading(true)
    setError(null)

    api
      .campaign(datasetId, activeId)
      .then((data) => {
        if (!cancelled) {
          setDetail(data)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [datasetId, activeId])

  const activeCamp = campaigns.find((c) => c.id === activeId) || campaigns[0]
  if (!activeCamp) {
    return <div className="p-8 text-center text-muted">No campaigns available to display.</div>
  }

  const handleSelectCamp = (id) => {
    setActiveId(id)
    onSelect?.(id)
  }

  const seeds = detail?.seeds || []
  const amplifiers = detail?.amplifiers || []
  const reach = detail?.reach || {}
  const assessment = activeCamp.assessment

  return (
    <div className="space-y-6">
      {/* 1. Campaign Selection Tabs */}
      <div className="flex flex-wrap items-center gap-2 pb-2 border-b border-line">
        <span className="text-xs font-semibold text-muted uppercase tracking-wider mr-1">
          Select Campaign:
        </span>
        {campaigns.map((c) => {
          const isActive = c.id === activeId
          const color = campaignColor(c.id)
          return (
            <button
              key={c.id}
              onClick={() => handleSelectCamp(c.id)}
              className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
                isActive
                  ? 'bg-subtle text-ink border-line shadow-xs font-semibold'
                  : 'bg-surface text-muted border-line/60 hover:text-ink hover:border-line'
              }`}
            >
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ background: color }}
              />
              <span>{c.id.toUpperCase()}</span>
              {c.top_hashtag && (
                <span className="font-mono text-muted text-[11px] truncate max-w-[130px]">
                  {c.top_hashtag}
                </span>
              )}
              {c.assessment?.level && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded font-semibold ${
                    c.assessment.level === 'URGENT'
                      ? 'bg-urgent-soft text-urgent'
                      : c.assessment.level === 'ALERT'
                      ? 'bg-alert-soft text-alert'
                      : 'bg-subtle text-muted'
                  }`}
                >
                  {c.assessment.level}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* 2. Key Metric Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-subtle/60 border border-line rounded-lg p-3.5">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-muted font-medium">
            Coordinated Size
          </div>
          <div className="text-lg font-semibold text-ink mt-0.5">
            {fmt(activeCamp.size)} accounts
          </div>
          <div className="text-[11px] text-muted">Synchronized action</div>
        </div>

        <div>
          <div className="text-[11px] uppercase tracking-wider text-muted font-medium">
            Spread Velocity
          </div>
          <div className="text-lg font-semibold text-ink mt-0.5 flex items-center gap-1.5">
            <Zap className="w-4 h-4 text-alert" />
            {reach.to_10_accounts_min != null ? `${reach.to_10_accounts_min} min` : 'Seconds'}
          </div>
          <div className="text-[11px] text-muted">To reach first 10 accounts</div>
        </div>

        <div>
          <div className="text-[11px] uppercase tracking-wider text-muted font-medium">
            90% Saturation
          </div>
          <div className="text-lg font-semibold text-ink mt-0.5 flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-accent" />
            {reach.to_90pct_min != null ? `${reach.to_90pct_min} min` : 'Fast burst'}
          </div>
          <div className="text-[11px] text-muted">To full campaign scale</div>
        </div>

        <div>
          <div className="text-[11px] uppercase tracking-wider text-muted font-medium">
            CIB Risk Score
          </div>
          <div className="text-lg font-semibold mt-0.5 flex items-center gap-1.5">
            <span
              className={
                activeCamp.cib_score >= 70
                  ? 'text-urgent'
                  : activeCamp.cib_score >= 40
                  ? 'text-alert'
                  : 'text-benign'
              }
            >
              {activeCamp.cib_score}/100
            </span>
            {activeCamp.assessment?.threat_type && (
              <span className="text-xs font-normal text-muted truncate">
                ({THREATS[activeCamp.assessment.threat_type] || activeCamp.assessment.threat_type})
              </span>
            )}
          </div>
          <div className="text-[11px] text-muted">Inauthentic behavior index</div>
        </div>
      </div>

      {loading && (
        <div className="py-12 flex flex-col items-center justify-center gap-2 text-muted text-sm">
          <Spinner className="w-5 h-5 text-accent" />
          <span>Tracing propagation stages...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-urgent-soft border border-urgent/20 rounded-lg text-sm text-urgent">
          Could not load complete flow details: {error}
        </div>
      )}

      {!loading && (
        <div className="relative">
          {/* Vertical connecting line for desktop flow */}
          <div
            className="hidden md:block absolute left-[27px] top-6 bottom-6 w-0.5 bg-gradient-to-b from-accent via-alert to-urgent"
            aria-hidden="true"
          />

          <div className="space-y-8">
            {/* ================= STAGE 1: INCEPTION (SEEDS) ================= */}
            <div className="relative pl-0 md:pl-16">
              {/* Step indicator node */}
              <div
                className="hidden md:flex absolute left-4 top-1 w-6 h-6 rounded-full bg-accent text-accent-ink items-center justify-center text-xs font-bold ring-4 ring-surface"
                aria-hidden="true"
              >
                1
              </div>

              <div className="bg-surface border border-line rounded-lg p-4 shadow-2xs space-y-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 text-xs font-semibold rounded bg-accent/10 text-accent uppercase tracking-wider">
                      Stage 1 · Origin
                    </span>
                    <h3 className="text-sm font-semibold text-ink">
                      Seed Accounts (Campaign Starters)
                    </h3>
                  </div>
                  <span className="text-xs text-muted">
                    {seeds.length} originator{seeds.length === 1 ? '' : 's'} identified
                  </span>
                </div>

                <p className="text-xs text-muted leading-relaxed">
                  These accounts initiated the narrative before any amplification occurred. They
                  represent the initial entry point of the coordinated campaign.
                </p>

                {seeds.length === 0 ? (
                  <div className="text-xs text-faint italic py-2">
                    No discrete seed accounts identified in preliminary logs.
                  </div>
                ) : (
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 pt-1">
                    {seeds.map((s, idx) => (
                      <div
                        key={s.account_id || idx}
                        className="bg-subtle/50 border border-line rounded-md p-3 space-y-2 hover:border-accent/40 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-1">
                          <button
                            onClick={() =>
                              onOpenPosts?.({
                                campaign: activeId,
                                account_id: s.account_id,
                              })
                            }
                            className="font-mono text-xs font-semibold text-ink hover:text-accent truncate text-left"
                            title={s.username || s.account_id}
                          >
                            @{s.username || s.account_id}
                          </button>
                          <span className="text-[10px] uppercase font-bold text-accent px-1.5 py-0.5 rounded bg-surface border border-line">
                            SEED #{idx + 1}
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
                          {s.platform && (
                            <span className="inline-flex items-center gap-1">
                              <Globe className="w-3 h-3 text-faint" />
                              {platformLabel(s.platform).label}
                            </span>
                          )}
                          {s.first_seen && (
                            <span className="inline-flex items-center gap-1 font-mono text-[10px]">
                              <Clock className="w-3 h-3 text-faint" />
                              {fmtClock(s.first_seen)}
                            </span>
                          )}
                        </div>

                        {s.text && (
                          <p className="text-[11px] text-ink/80 bg-surface/80 p-2 rounded border border-line/60 line-clamp-3 italic leading-snug">
                            &ldquo;{s.text}&rdquo;
                          </p>
                        )}

                        {s.account_age_days != null && (
                          <div className="text-[10px] text-faint">
                            Account age:{' '}
                            <span className="text-muted font-medium">
                              {s.account_age_days === 0
                                ? 'Created same day'
                                : `${s.account_age_days} days`}
                            </span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Transition indicator: Velocity */}
            <div className="relative pl-0 md:pl-16 flex items-center gap-3">
              <div className="bg-surface border border-line rounded-full px-3 py-1 text-xs text-muted flex items-center gap-2 shadow-2xs">
                <ArrowRight className="w-3.5 h-3.5 text-alert animate-pulse" />
                <span>
                  Synchronized surge within{' '}
                  <strong className="text-ink">
                    {reach.to_10_accounts_min != null ? `${reach.to_10_accounts_min}m` : 'seconds'}
                  </strong>{' '}
                  across key botnet nodes
                </span>
              </div>
            </div>

            {/* ================= STAGE 2: AMPLIFICATION ================= */}
            <div className="relative pl-0 md:pl-16">
              {/* Step indicator node */}
              <div
                className="hidden md:flex absolute left-4 top-1 w-6 h-6 rounded-full bg-alert text-surface items-center justify-center text-xs font-bold ring-4 ring-surface"
                aria-hidden="true"
              >
                2
              </div>

              <div className="bg-surface border border-line rounded-lg p-4 shadow-2xs space-y-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 text-xs font-semibold rounded bg-alert/10 text-alert uppercase tracking-wider">
                      Stage 2 · Amplification
                    </span>
                    <h3 className="text-sm font-semibold text-ink">
                      Core Amplifiers &amp; Botnet Nodes
                    </h3>
                  </div>
                  <span className="text-xs text-muted">
                    {amplifiers.length} high-degree amplifier{amplifiers.length === 1 ? '' : 's'}
                  </span>
                </div>

                <p className="text-xs text-muted leading-relaxed">
                  These accounts repeatedly posted or retweeted in locked synchrony with the seeds,
                  amplifying message volume and evading single-account velocity limits.
                </p>

                {amplifiers.length === 0 ? (
                  <div className="text-xs text-faint italic py-2">
                    Amplifier accounts are participating uniformly across the campaign community.
                  </div>
                ) : (
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 pt-1">
                    {amplifiers.map((a, idx) => (
                      <div
                        key={a.account_id || idx}
                        className="bg-subtle/50 border border-line rounded-md p-3 space-y-2 hover:border-alert/40 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-1">
                          <button
                            onClick={() =>
                              onOpenPosts?.({
                                campaign: activeId,
                                account_id: a.account_id,
                              })
                            }
                            className="font-mono text-xs font-semibold text-ink hover:text-alert truncate text-left"
                            title={a.username || a.account_id}
                          >
                            @{a.username || a.account_id}
                          </button>
                          <span className="text-[10px] font-mono bg-alert-soft text-alert px-1.5 py-0.2 rounded font-semibold">
                            {a.links} links
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-1.5 text-xs pt-1">
                          <div className="bg-surface p-1.5 rounded border border-line/60">
                            <div className="text-[10px] text-muted">Campaign Posts</div>
                            <div className="font-semibold text-ink">{fmt(a.posts)}</div>
                          </div>
                          <div className="bg-surface p-1.5 rounded border border-line/60">
                            <div className="text-[10px] text-muted">Co-actions</div>
                            <div className="font-semibold text-ink">{a.links} connections</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Signals breakdown */}
                {activeCamp.signals?.length > 0 && (
                  <div className="pt-2 border-t border-line/60">
                    <div className="text-[11px] font-semibold text-muted uppercase tracking-wider mb-2">
                      Tactics &amp; Coordination Signals Used:
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {activeCamp.signals.map((sig) => (
                        <div
                          key={sig}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface border border-line text-xs"
                          title={SIGNAL_DESC[sig] || sig}
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-alert" />
                          <span className="font-medium text-ink">{SIGNALS[sig] || sig}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Transition indicator: Cross-Channel Spread */}
            <div className="relative pl-0 md:pl-16 space-y-2">
              {detail?.platform_path && detail.platform_path.length > 1 && (
                <div className="bg-surface border border-line rounded-lg p-3 shadow-2xs space-y-1.5">
                  <div className="text-[11px] uppercase tracking-wider font-semibold text-muted flex items-center gap-1.5">
                    <Share2 className="w-3.5 h-3.5 text-accent" />
                    Cross-Platform Hop Sequence:
                  </div>
                  <SpreadPath path={detail.platform_path} kind="platform" />
                </div>
              )}

              {detail?.town_path && detail.town_path.length > 1 && (
                <div className="bg-surface border border-line rounded-lg p-3 shadow-2xs space-y-1.5">
                  <div className="text-[11px] uppercase tracking-wider font-semibold text-muted flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-urgent" />
                    Geographic Hop Sequence:
                  </div>
                  <SpreadPath path={detail.town_path} kind="town" />
                </div>
              )}
            </div>

            {/* ================= STAGE 3: PUBLIC DIFFUSION & IMPACT ================= */}
            <div className="relative pl-0 md:pl-16">
              {/* Step indicator node */}
              <div
                className="hidden md:flex absolute left-4 top-1 w-6 h-6 rounded-full bg-urgent text-surface items-center justify-center text-xs font-bold ring-4 ring-surface"
                aria-hidden="true"
              >
                3
              </div>

              <div className="bg-surface border border-line rounded-lg p-4 shadow-2xs space-y-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 text-xs font-semibold rounded bg-urgent/10 text-urgent uppercase tracking-wider">
                      Stage 3 · Public Impact
                    </span>
                    <h3 className="text-sm font-semibold text-ink">
                      Target Audience &amp; Real-World Diffusion
                    </h3>
                  </div>
                  {assessment?.threat_type && (
                    <Badge tone={assessment.level === 'URGENT' ? 'URGENT' : 'ALERT'}>
                      {THREATS[assessment.threat_type] || assessment.threat_type}
                    </Badge>
                  )}
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="p-3 bg-subtle/50 rounded-md border border-line space-y-1.5">
                    <div className="text-xs font-semibold text-ink">Campaign Reach Metrics</div>
                    <ul className="text-xs text-muted space-y-1">
                      <li>
                        Total accounts engaged: <strong>{fmt(activeCamp.size)}</strong>
                      </li>
                      <li>
                        Time to 90% saturation:{' '}
                        <strong>
                          {reach.to_90pct_min != null ? `${reach.to_90pct_min} minutes` : 'Rapid'}
                        </strong>
                      </li>
                      {detail?.languages && (
                        <li>
                          Languages detected:{' '}
                          <strong>
                            {Object.keys(detail.languages)
                              .map((l) => langLabel(l))
                              .join(', ')}
                          </strong>
                        </li>
                      )}
                    </ul>
                  </div>

                  {assessment?.offline_event?.at ? (
                    <div className="p-3 bg-urgent-soft/60 border border-urgent/30 rounded-md space-y-1.5 text-urgent">
                      <div className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                        <Flame className="w-3.5 h-3.5" />
                        Call to Gather Detected!
                      </div>
                      <div className="text-xs">
                        Location: <strong>{assessment.offline_event.where}</strong>
                      </div>
                      <div className="text-xs">
                        Time: <strong>{fmtDay(assessment.offline_event.at)}</strong>
                      </div>
                      <div className="text-[11px] opacity-90">
                        Urgent escalation recommended due to physical crowd mobilization risk.
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-subtle/50 rounded-md border border-line space-y-1.5">
                      <div className="text-xs font-semibold text-ink">Online Sphere Status</div>
                      <p className="text-xs text-muted">
                        No physical crowd mobilization detected. The campaign operates purely as an
                        online information manipulation effort.
                      </p>
                    </div>
                  )}
                </div>

                {/* Footer Action buttons */}
                <div className="pt-3 border-t border-line/60 flex flex-wrap items-center justify-between gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => onOpenPosts?.({ campaign: activeId })}
                    className="text-xs"
                  >
                    <MessageSquare className="w-3.5 h-3.5 mr-1" />
                    Inspect All {fmt(activeCamp.size)} Accounts&apos; Posts
                  </Button>

                  <Button
                    variant="secondary"
                    onClick={onSwitchToGraph}
                    className="text-xs text-accent"
                  >
                    <Compass className="w-3.5 h-3.5 mr-1" />
                    View in Interactive Graph
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
