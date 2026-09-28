import React, { useEffect, useMemo, useRef, useState } from 'react'
import {
  AlertTriangle,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Bot,
  Calendar,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Copy,
  ExternalLink,
  Eye,
  FileCheck,
  FileText,
  Filter,
  Layers,
  MapPin,
  Network,
  Phone,
  Printer,
  RefreshCw,
  Search,
  Share2,
  Shield,
  ShieldAlert,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Users,
} from 'lucide-react'
import { api } from '../api'
import { Badge, Button, Card, Label, LevelBadge, ScoreBar, Spinner } from '../ui'
import { LangChips, PlatformChip, PlatformChips } from '../components/Chips'
import { SpreadPath } from '../components/SpreadPath'
import {
  campaignColor,
  FEATURES,
  SIGNALS,
  THREATS,
  fmt,
  fmtClock,
  fmtDate,
  fmtDay,
  fmtGap,
  fmtRange,
  fmtWhen,
  getDisplayZone,
  langLabel,
  platformLabel,
  zoneLabel,
} from '../labels'

// Formats unix timestamp with seconds e.g. "11:45:03" in the dataset's timezone
function fmtClockSeconds(t) {
  return new Date(t * 1000).toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: getDisplayZone(),
  })
}

// 8-stage SOC Architecture pipeline definitions
const PIPELINE_STAGES = [
  { id: 1, title: 'Social Media Data', desc: 'X, Telegram, WhatsApp ingestion', tech: 'Multi-platform API' },
  { id: 2, title: 'Data Processing', desc: 'Normalization & tokenization', tech: 'Streaming DB' },
  { id: 3, title: 'Coordination Detection', desc: 'Temporal bursts & similarity', tech: 'Cosine / MinHash' },
  { id: 4, title: 'Network Analysis', desc: 'Community & actor graph', tech: 'NetworkX & Louvain' },
  { id: 5, title: 'Risk / CIB Score', desc: '0–100 composite scoring', tech: '6-factor heuristics' },
  { id: 6, title: 'IBM Bob', desc: 'Semantic threat & intent AI', tech: 'Bob LLM Shell' },
  { id: 7, title: 'Investigator Review', desc: 'Human-in-the-loop validation', tech: 'SOC Console' },
  { id: 8, title: 'Evidence Report', desc: 'Section 63 BSA audit brief', tech: 'SHA-256 Hashes' },
]

export function BriefView({
  dataset,
  campaigns = [],
  timeline,
  stats,
  bobConfigured,
  onAssessed,
  onFilter = () => {},
  selectedCampaignId = null,
  onSelectCampaign = () => {},
  url,
}) {
  const [mode, setMode] = useState('console') // 'console' | 'report'
  const [activeCid, setActiveCid] = useState(selectedCampaignId)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all') // 'all' | 'URGENT' | 'ALERT' | 'MONITOR' | 'PENDING'
  const [sortBy, setSortBy] = useState('score') // 'score' | 'accounts' | 'earliest' | 'latest'
  const [copiedHash, setCopiedHash] = useState(null)
  const frameRef = useRef(null)
  const [reportLoading, setReportLoading] = useState(true)

  // Keep activeCid in sync if external selection changes
  useEffect(() => {
    if (selectedCampaignId && selectedCampaignId !== activeCid) {
      setActiveCid(selectedCampaignId)
    }
  }, [selectedCampaignId])

  const copyHash = (hash) => {
    if (!hash) return
    navigator.clipboard.writeText(hash).then(() => {
      setCopiedHash(hash)
      setTimeout(() => setCopiedHash(null), 2000)
    })
  }

  // Filter and sort campaigns for Campaign Management
  const filteredCampaigns = useMemo(() => {
    if (!campaigns || !campaigns.length) return []
    return campaigns
      .filter((c) => {
        const q = searchQuery.toLowerCase().trim()
        const matchesQuery =
          !q ||
          c.id.toLowerCase().includes(q) ||
          (c.top_hashtag && c.top_hashtag.toLowerCase().includes(q)) ||
          (c.accounts && c.accounts.some((a) => a.toLowerCase().includes(q)))

        if (!matchesQuery) return false

        if (statusFilter === 'all') return true
        if (statusFilter === 'PENDING') return !c.assessment
        return c.assessment?.level === statusFilter
      })
      .sort((a, b) => {
        if (sortBy === 'score') return b.score - a.score
        if (sortBy === 'accounts') return b.size - a.size
        if (sortBy === 'earliest') return a.first_seen - b.first_seen
        if (sortBy === 'latest') return b.first_seen - a.first_seen
        return 0
      })
  }, [campaigns, searchQuery, statusFilter, sortBy])

  // KPIs
  const totalCampaigns = campaigns?.length ?? 0
  const totalAccounts = useMemo(() => campaigns?.reduce((sum, c) => sum + (c.size || 0), 0) ?? 0, [campaigns])
  const highestScored = useMemo(() => {
    if (!campaigns || !campaigns.length) return null
    return [...campaigns].sort((a, b) => b.score - a.score)[0]
  }, [campaigns])
  const classifiedCount = useMemo(() => campaigns?.filter((c) => c.assessment).length ?? 0, [campaigns])

  const handleSelectCampaign = (cid) => {
    setActiveCid(cid)
    onSelectCampaign(cid)
  }

  const handleBackToManagement = () => {
    setActiveCid(null)
    onSelectCampaign(null)
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Mode Toggle Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-surface border border-line rounded-lg p-3 px-4 shadow-xs">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-accent" />
          <div>
            <h1 className="text-sm font-semibold text-ink">Threat Escalation Brief &amp; Investigation Console</h1>
            <p className="text-xs text-muted">
              Section 63 BSA evidentiary audit &amp; coordinated inauthentic behavior triage
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-md border border-line bg-subtle p-0.5 text-xs">
            <button
              onClick={() => setMode('console')}
              className={`px-3 py-1 rounded cursor-pointer font-medium transition-colors ${
                mode === 'console' ? 'bg-surface text-ink shadow-xs' : 'text-muted hover:text-ink'
              }`}
            >
              Investigation Console
            </button>
            <button
              onClick={() => setMode('report')}
              className={`px-3 py-1 rounded cursor-pointer font-medium transition-colors ${
                mode === 'report' ? 'bg-surface text-ink shadow-xs' : 'text-muted hover:text-ink'
              }`}
            >
              Printable PDF Brief
            </button>
          </div>

          <Button
            onClick={() => {
              const targetUrl = activeCid ? api.briefUrl(dataset.id, activeCid) : url
              window.open(targetUrl, '_blank', 'noopener')
            }}
            title="Open generated brief document in a new browser tab"
          >
            <ExternalLink className="w-4 h-4" /> Open Document
          </Button>

          <Button
            variant="primary"
            onClick={() => {
              if (mode === 'report' && frameRef.current?.contentWindow) {
                frameRef.current.contentWindow.print()
              } else {
                const targetUrl = activeCid ? api.briefUrl(dataset.id, activeCid) : url
                const w = window.open(targetUrl, '_blank')
                if (w) {
                  w.onload = () => w.print()
                }
              }
            }}
          >
            <Printer className="w-4 h-4" /> Print / Save PDF
          </Button>
        </div>
      </div>

      {/* Mode 1: Printable Report Preview (Iframe) */}
      {mode === 'report' && (
        <div className="relative bg-surface border border-line rounded-lg overflow-hidden shadow-xs">
          <div className="flex items-center justify-between px-4 py-2 bg-subtle border-b border-line text-xs text-muted">
            <span>
              Previewing: <strong>{activeCid ? `Campaign ${activeCid.toUpperCase()} Investigation Brief` : 'Master Executive Threat Escalation Brief'}</strong>
            </span>
            {activeCid && (
              <button
                onClick={() => setActiveCid(null)}
                className="text-accent cursor-pointer hover:underline"
              >
                Switch to All Campaigns Brief
              </button>
            )}
          </div>
          {reportLoading && (
            <div className="absolute inset-0 flex items-center justify-center gap-2 text-sm text-muted bg-surface/80 z-10">
              <Spinner /> Generating Section 63 BSA threat escalation brief…
            </div>
          )}
          <iframe
            ref={frameRef}
            key={`${activeCid || 'all'}-${url}`}
            src={activeCid ? api.briefUrl(dataset.id, activeCid) : url}
            title="Threat Brief PDF Preview"
            onLoad={() => setReportLoading(false)}
            className="block w-full h-[calc(100vh-220px)] min-h-[700px] bg-white"
          />
        </div>
      )}

      {/* Mode 2: Interactive Threat Intelligence & Campaign Investigation */}
      {mode === 'console' && (
        <>
          {activeCid ? (
            /* Dedicated Individual Campaign Investigation View (Sections A through I) */
            <CampaignInvestigationView
              dataset={dataset}
              campaignId={activeCid}
              allCampaigns={campaigns}
              bobConfigured={bobConfigured}
              onBack={handleBackToManagement}
              onSelectCampaign={handleSelectCampaign}
              onAssessed={onAssessed}
              onFilter={onFilter}
              onCopyHash={copyHash}
              copiedHash={copiedHash}
              onOpenPrint={() => setMode('report')}
            />
          ) : (
            /* Master Threat Intelligence Dashboard & Campaign Management */
            <div className="space-y-6">
              {/* ==================================================
                  1. EXECUTIVE THREAT INTELLIGENCE DASHBOARD
                  ================================================== */}
              <section className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold tracking-wider text-muted uppercase">
                    Executive Threat Intelligence Dashboard
                  </h2>
                  <span className="text-xs text-muted font-mono">
                    Timezone: {zoneLabel()} · Data-Driven SOC Hierarchy
                  </span>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-surface border border-line rounded-lg p-4 shadow-2xs">
                    <div className="flex items-center justify-between text-muted mb-1">
                      <span className="text-xs font-medium uppercase tracking-wider">Total Campaigns</span>
                      <Layers className="w-4 h-4 text-accent" />
                    </div>
                    <div className="text-3xl font-semibold font-mono text-ink">{totalCampaigns}</div>
                    <div className="text-xs text-muted mt-1">Identified CIB clusters</div>
                  </div>

                  <div className="bg-surface border border-line rounded-lg p-4 shadow-2xs">
                    <div className="flex items-center justify-between text-muted mb-1">
                      <span className="text-xs font-medium uppercase tracking-wider">Total Accounts</span>
                      <Users className="w-4 h-4 text-accent" />
                    </div>
                    <div className="text-3xl font-semibold font-mono text-ink">{fmt(totalAccounts)}</div>
                    <div className="text-xs text-muted mt-1">Coordinated participating actors</div>
                  </div>

                  <div className="bg-surface border border-line rounded-lg p-4 shadow-2xs">
                    <div className="flex items-center justify-between text-muted mb-1">
                      <span className="text-xs font-medium uppercase tracking-wider">Highest CIB Score</span>
                      <ShieldAlert className="w-4 h-4 text-urgent" />
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-semibold font-mono text-urgent">
                        {highestScored ? highestScored.score : 0}
                      </span>
                      <span className="text-xs text-muted font-mono">/ 100</span>
                    </div>
                    <div className="text-xs text-muted mt-1 truncate">
                      {highestScored ? (
                        <span className="font-mono font-medium text-ink">
                          {highestScored.id.toUpperCase()} {highestScored.top_hashtag || ''}
                        </span>
                      ) : (
                        'No campaigns'
                      )}
                    </div>
                  </div>

                  <div className="bg-surface border border-line rounded-lg p-4 shadow-2xs">
                    <div className="flex items-center justify-between text-muted mb-1">
                      <span className="text-xs font-medium uppercase tracking-wider">IBM Bob Classification</span>
                      <Bot className="w-4 h-4 text-accent" />
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-semibold font-mono text-ink">{classifiedCount}</span>
                      <span className="text-xs text-muted">/ {totalCampaigns} classified</span>
                    </div>
                    <div className="text-xs text-muted mt-1">
                      {totalCampaigns - classifiedCount === 0
                        ? 'All campaigns classified'
                        : `${totalCampaigns - classifiedCount} pending Bob evaluation`}
                    </div>
                  </div>
                </div>

                {/* ==================================================
                    5. SYSTEM ARCHITECTURE VISUAL (8-Stage SOC Pipeline)
                    ================================================== */}
                <div className="bg-surface border border-line rounded-lg p-4 space-y-3 shadow-2xs">
                  <div className="flex items-center justify-between border-b border-line pb-2">
                    <div className="flex items-center gap-2">
                      <Network className="w-4 h-4 text-accent" />
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
                        Threat Detection Architecture &amp; Analysis Pipeline
                      </h3>
                    </div>
                    <span className="text-[11px] text-faint">End-to-End Auditable Triage</span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2">
                    {PIPELINE_STAGES.map((s, idx) => (
                      <div
                        key={s.id}
                        className="relative flex flex-col justify-between p-2.5 rounded-md border border-line bg-subtle/50 text-xs"
                      >
                        <div>
                          <div className="flex items-center justify-between text-[10px] font-mono text-muted mb-1">
                            <span>0{s.id}</span>
                            {idx < PIPELINE_STAGES.length - 1 && (
                              <ArrowRight className="hidden lg:block w-3 h-3 text-faint" />
                            )}
                          </div>
                          <div className="font-semibold text-ink text-[11px] leading-snug">{s.title}</div>
                          <div className="text-[10px] text-muted mt-0.5 leading-tight">{s.desc}</div>
                        </div>
                        <div className="mt-2 pt-1 border-t border-line/60 text-[9px] font-mono text-accent">
                          {s.tech}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              {/* ==================================================
                  2. CAMPAIGN MANAGEMENT
                  ================================================== */}
              <section className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold text-ink">Campaign Management</h2>
                    <p className="text-xs text-muted">
                      Select any campaign to drill down into deep investigation, evidence records, and IBM Bob assessment.
                    </p>
                  </div>

                  {/* Search, Filter, Sort Controls */}
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Search */}
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted" />
                      <input
                        type="text"
                        placeholder="Search campaigns, hashtags, accounts…"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="h-8 pl-8 pr-3 text-xs bg-surface border border-line rounded-md text-ink placeholder:text-muted focus:outline-accent w-48 sm:w-64"
                      />
                    </div>

                    {/* Status Filter */}
                    <div className="flex items-center gap-1 text-xs text-muted">
                      <Filter className="w-3.5 h-3.5 text-muted" />
                      <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="h-8 px-2 text-xs bg-surface border border-line rounded-md text-ink cursor-pointer focus:outline-accent"
                      >
                        <option value="all">Status: All</option>
                        <option value="URGENT">Status: URGENT</option>
                        <option value="ALERT">Status: ALERT</option>
                        <option value="MONITOR">Status: MONITOR</option>
                        <option value="PENDING">Status: Pending IBM Bob</option>
                      </select>
                    </div>

                    {/* Sort Filter */}
                    <div className="flex items-center gap-1 text-xs text-muted">
                      <SlidersHorizontal className="w-3.5 h-3.5 text-muted" />
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="h-8 px-2 text-xs bg-surface border border-line rounded-md text-ink cursor-pointer focus:outline-accent"
                      >
                        <option value="score">Sort: CIB Score (High → Low)</option>
                        <option value="accounts">Sort: Account Count (High → Low)</option>
                        <option value="earliest">Sort: Earliest Detected</option>
                        <option value="latest">Sort: Latest Detected</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Campaign Cards List */}
                {filteredCampaigns.length === 0 ? (
                  <div className="bg-surface border border-line rounded-lg p-10 text-center text-sm text-muted">
                    No coordinated campaigns match your search or filter criteria.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredCampaigns.map((c) => {
                      const color = campaignColor(c.id)
                      const level = c.assessment?.level
                      const platforms = c.platform_path?.map((p) => p.name) || []
                      const location = c.town_path?.length
                        ? c.town_path.map((t) => t.name).join(' → ')
                        : 'Delhi / Multi-city'

                      return (
                        <div
                          key={c.id}
                          className="bg-surface border border-line hover:border-line/80 rounded-lg p-4 transition-shadow hover:shadow-xs"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            {/* Campaign Identity & Hashtag */}
                            <div className="flex items-center gap-3 min-w-0">
                              <span
                                className="w-3.5 h-3.5 rounded-full shrink-0"
                                style={{ background: color }}
                              />
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="font-mono font-bold text-sm text-ink uppercase">
                                    Campaign {c.id}
                                  </span>
                                  {c.top_hashtag && (
                                    <span className="text-sm font-semibold text-accent truncate max-w-xs">
                                      {c.top_hashtag}
                                    </span>
                                  )}
                                  <LevelBadge level={level} />
                                </div>
                                <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-muted">
                                  <span>
                                    <strong className="text-ink">{fmt(c.size)}</strong> Accounts
                                  </span>
                                  <span>·</span>
                                  <span>{location}</span>
                                  {platforms.length > 0 && (
                                    <>
                                      <span>·</span>
                                      <span className="text-ink font-mono text-[11px]">
                                        {platforms.map((p) => platformLabel(p).label).join(' → ')}
                                      </span>
                                    </>
                                  )}
                                  {c.detected_at && (
                                    <>
                                      <span>·</span>
                                      <span>
                                        Flagged at <strong className="text-ink">{fmtClock(c.detected_at)}</strong>
                                      </span>
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Score & View Button */}
                            <div className="flex items-center gap-6">
                              <div className="text-right w-32 shrink-0">
                                <div className="flex items-baseline justify-end gap-1">
                                  <span className="text-lg font-bold font-mono text-ink">{c.score}</span>
                                  <span className="text-xs text-muted font-mono">/ 100</span>
                                </div>
                                <ScoreBar value={c.score} max={100} color={color} />
                              </div>

                              <Button
                                variant="primary"
                                onClick={() => handleSelectCampaign(c.id)}
                                className="cursor-pointer"
                              >
                                View Investigation <ArrowRight className="w-3.5 h-3.5" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </section>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ==================================================
// 3. INDIVIDUAL CAMPAIGN INVESTIGATION VIEW (A through I)
// ==================================================
function CampaignInvestigationView({
  dataset,
  campaignId,
  allCampaigns,
  bobConfigured,
  onBack,
  onSelectCampaign,
  onAssessed,
  onFilter,
  onCopyHash,
  copiedHash,
  onOpenPrint,
}) {
  const [campaign, setCampaign] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState(null)

  // Evidence controls
  const [showAllEvidence, setShowAllEvidence] = useState(false)
  const [evidenceSearch, setEvidenceSearch] = useState('')
  const [evidencePlatform, setEvidencePlatform] = useState('all')
  const [evidenceSort, setEvidenceSort] = useState('earliest')
  const [expandedPostIds, setExpandedPostIds] = useState(new Set())

  // Load campaign details & verdict
  useEffect(() => {
    setLoading(true)
    setError(null)
    setCampaign(null)
    setResult(null)

    let cancelled = false
    Promise.all([
      api.campaign(dataset.id, campaignId),
      api.verdict(dataset.id, campaignId).catch(() => null),
    ])
      .then(([c, v]) => {
        if (cancelled) return
        setCampaign(c)
        setResult(v)
      })
      .catch((e) => {
        if (!cancelled) setError(e.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [dataset.id, campaignId])

  const askBob = async () => {
    setAsking(true)
    setError(null)
    try {
      const r = await api.classify(dataset.id, campaignId)
      onAssessed(campaignId, {
        threat_type: r.verdict.threat_type,
        severity: r.verdict.severity,
        level: r.escalation.level,
        offline_event: r.verdict.offline_event,
      })
      setResult(r)
    } catch (e) {
      setError(e.message)
    } finally {
      setAsking(false)
    }
  }

  const toggleExpandPost = (postId) => {
    setExpandedPostIds((prev) => {
      const next = new Set(prev)
      if (next.has(postId)) next.delete(postId)
      else next.add(postId)
      return next
    })
  }

  if (loading) {
    return (
      <div className="bg-surface border border-line rounded-lg p-12 flex flex-col items-center justify-center gap-3 text-muted">
        <Spinner className="w-6 h-6 text-accent" />
        <p className="text-sm font-medium">Loading Campaign {campaignId.toUpperCase()} evidence &amp; telemetry…</p>
      </div>
    )
  }

  if (error || !campaign) {
    return (
      <div className="bg-surface border border-line rounded-lg p-8 text-center space-y-3">
        <p className="text-urgent text-sm font-medium">Failed to load campaign: {error || 'Campaign not found'}</p>
        <Button onClick={onBack}>
          <ArrowLeft className="w-4 h-4" /> Back to Campaign Management
        </Button>
      </div>
    )
  }

  const color = campaignColor(campaign.id)
  const verdict = result?.verdict
  const escalation = result?.escalation
  const level = escalation?.level || 'PENDING'
  const event = verdict?.offline_event
  const evidenceSet = new Set(verdict?.evidence_post_ids || [])
  const span = (campaign.last_seen || 0) - (campaign.first_seen || 0)
  const reach = campaign.reach || {}

  // Filtered evidence records
  const samplePosts = campaign.sample_posts || []
  const filteredEvidence = samplePosts
    .filter((p) => {
      const q = evidenceSearch.toLowerCase().trim()
      const postHash = p.sha256_hash || p.sha256 || ''
      const matchesSearch =
        !q ||
        p.post_id?.toLowerCase().includes(q) ||
        p.username?.toLowerCase().includes(q) ||
        p.text?.toLowerCase().includes(q) ||
        postHash.toLowerCase().includes(q)

      if (!matchesSearch) return false
      if (evidencePlatform !== 'all' && p.platform?.toLowerCase() !== evidencePlatform.toLowerCase())
        return false
      return true
    })
    .sort((a, b) => {
      if (evidenceSort === 'earliest') return (a.created_at || 0) - (b.created_at || 0)
      return (b.created_at || 0) - (a.created_at || 0)
    })

  return (
    <div className="space-y-6">
      {/* -----------------------------------------
          A. CAMPAIGN HEADER
          ----------------------------------------- */}
      <div className="bg-surface border border-line rounded-lg p-4 shadow-xs space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Button onClick={onBack} variant="ghost" className="h-8 px-2 text-xs">
              <ArrowLeft className="w-4 h-4" /> Back to Campaigns
            </Button>

            {/* Campaign Selector Dropdown */}
            <div className="flex items-center gap-1.5 pl-2 border-l border-line">
              <span className="w-3 h-3 rounded-full shrink-0" style={{ background: color }} />
              <select
                value={campaign.id}
                onChange={(e) => onSelectCampaign(e.target.value)}
                className="h-8 font-mono font-bold text-sm bg-surface border border-line rounded px-2 cursor-pointer focus:outline-accent"
              >
                {allCampaigns.map((c) => (
                  <option key={c.id} value={c.id}>
                    Campaign {c.id.toUpperCase()} {c.top_hashtag ? `(${c.top_hashtag})` : ''}
                  </option>
                ))}
              </select>
            </div>

            {campaign.top_hashtag && (
              <span className="text-base font-semibold text-accent">
                {campaign.top_hashtag}
              </span>
            )}

            <LevelBadge level={verdict ? level : null} />
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={() => onFilter({ campaign: campaign.id })}
              title="Open full Posts view filtered to this campaign"
            >
              <Eye className="w-4 h-4" /> View All Posts ({fmt(campaign.post_count)})
            </Button>
            <Button variant="primary" onClick={onOpenPrint}>
              <Printer className="w-4 h-4" /> Generate Brief PDF
            </Button>
          </div>
        </div>
      </div>

      {/* -----------------------------------------
          B. CAMPAIGN OVERVIEW METADATA CARDS
          ----------------------------------------- */}
      <section className="space-y-2">
        <Label>B. Campaign Overview</Label>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
          <div className="bg-surface border border-line rounded-md p-3">
            <div className="text-[11px] text-muted uppercase tracking-wider">Campaign</div>
            <div className="text-base font-bold font-mono text-ink mt-0.5">{campaign.id.toUpperCase()}</div>
          </div>
          <div className="bg-surface border border-line rounded-md p-3">
            <div className="text-[11px] text-muted uppercase tracking-wider">Accounts</div>
            <div className="text-base font-bold font-mono text-ink mt-0.5">{fmt(campaign.size)}</div>
          </div>
          <div className="bg-surface border border-line rounded-md p-3">
            <div className="text-[11px] text-muted uppercase tracking-wider">Platforms</div>
            <div className="text-sm font-semibold text-ink mt-0.5 truncate">
              {campaign.platform_path?.length
                ? campaign.platform_path.map((p) => platformLabel(p.name).short).join(' → ')
                : 'Social'}
            </div>
          </div>
          <div className="bg-surface border border-line rounded-md p-3">
            <div className="text-[11px] text-muted uppercase tracking-wider">Location</div>
            <div className="text-sm font-semibold text-ink mt-0.5 truncate">
              {campaign.town_path?.length
                ? campaign.town_path.map((t) => t.name).join(', ')
                : 'Delhi / Multi-city'}
            </div>
          </div>
          <div className="bg-surface border border-line rounded-md p-3">
            <div className="text-[11px] text-muted uppercase tracking-wider">First Detected</div>
            <div className="text-xs font-mono font-medium text-ink mt-0.5">
              {fmtClock(campaign.first_seen)}
            </div>
          </div>
          <div className="bg-surface border border-line rounded-md p-3">
            <div className="text-[11px] text-muted uppercase tracking-wider">Flagged At</div>
            <div className="text-xs font-mono font-medium text-ink mt-0.5">
              {campaign.detected_at ? fmtClock(campaign.detected_at) : '—'}
            </div>
          </div>
          <div className="bg-surface border border-line rounded-md p-3">
            <div className="text-[11px] text-muted uppercase tracking-wider">CIB Score</div>
            <div className="text-base font-bold font-mono text-urgent mt-0.5">{campaign.score}/100</div>
          </div>
          <div className="bg-surface border border-line rounded-md p-3">
            <div className="text-[11px] text-muted uppercase tracking-wider">Bob Status</div>
            <div className="text-xs font-semibold text-ink mt-0.5">
              {verdict ? level : 'Pending Bob'}
            </div>
          </div>
        </div>
      </section>

      {/* Grid: How It Spread & Why It Was Flagged */}
      <div className="grid gap-6 lg:grid-cols-12 items-start">
        {/* -----------------------------------------
            C. HOW IT SPREAD (TIMELINE & FLOW VISUAL)
            ----------------------------------------- */}
        <div className="lg:col-span-7 bg-surface border border-line rounded-lg p-5 space-y-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-line pb-2">
            <div className="flex items-center gap-2">
              <Share2 className="w-4 h-4 text-accent" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
                C. How It Spread (Cross-Platform Propagation Flow)
              </h3>
            </div>
            {campaign.platform_path?.length > 1 && (
              <span className="text-xs font-mono text-muted">
                {campaign.platform_path.map((p) => platformLabel(p.name).label).join(' → ')}
              </span>
            )}
          </div>

          {/* High-level Platform / Town Path */}
          {campaign.platform_path?.length > 1 && (
            <div className="space-y-1">
              <div className="text-xs text-muted">Platform Progression Order:</div>
              <SpreadPath path={campaign.platform_path} kind="platform" span={span} />
            </div>
          )}

          {/* Second-by-Second Flow Visualization Node Stream */}
          <div className="space-y-2">
            <div className="text-xs font-medium text-muted">
              Temporal Cascade (Chronological Ingestion &amp; Amplification Sequence):
            </div>
            <div className="relative pl-6 space-y-3 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-line">
              {samplePosts.slice(0, 6).map((post, idx) => {
                const isLast = idx === Math.min(samplePosts.length, 6) - 1
                return (
                  <div key={post.post_id || idx} className="relative">
                    {/* Flow Pin / Arrow Indicator */}
                    <div
                      className="absolute -left-6 top-1 w-3.5 h-3.5 rounded-full border-2 border-surface flex items-center justify-center text-[8px] text-white"
                      style={{ background: color }}
                    >
                      •
                    </div>

                    <div className="rounded-md border border-line bg-subtle/40 p-2.5 text-xs space-y-1">
                      <div className="flex flex-wrap items-center justify-between gap-1">
                        <div className="flex items-center gap-1.5 font-mono">
                          <strong className="text-ink font-bold">
                            {fmtClockSeconds(post.created_at)}
                          </strong>
                          {post.platform && <PlatformChip platform={post.platform} />}
                          <button
                            onClick={() => onFilter({ account: post.account_id })}
                            className="font-medium text-accent hover:underline cursor-pointer truncate max-w-[140px]"
                          >
                            @{post.username || post.account_id}
                          </button>
                        </div>
                        {post.city && <span className="text-muted text-[11px]">📍 {post.city}</span>}
                      </div>
                      <p className="text-muted text-xs line-clamp-2 italic">“{post.text}”</p>
                    </div>

                    {/* Down connector arrow */}
                    {!isLast && (
                      <div className="flex justify-center -mb-2 mt-1">
                        <ArrowDown className="w-3.5 h-3.5 text-faint" />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Velocity & Reach Metrics */}
          <div className="pt-2 border-t border-line text-xs text-muted space-y-1">
            {reach.to_10_accounts_min != null && (
              <p>
                ⚡ <strong>10 accounts</strong> synchronized within{' '}
                <strong className="text-ink font-mono">{fmtGap(reach.to_10_accounts_min * 60)}</strong> of the first post.
              </p>
            )}
            {reach.to_90pct_min != null && (
              <p>
                🌐 <strong>90% of campaign accounts</strong> active within{' '}
                <strong className="text-ink font-mono">{fmtGap(reach.to_90pct_min * 60)}</strong>.
              </p>
            )}
            {campaign.new_account_share != null && (
              <p>
                ⚠️ <strong>{Math.round(campaign.new_account_share * 100)}%</strong> of participating accounts created under 30 days prior.
              </p>
            )}
          </div>
        </div>

        {/* -----------------------------------------
            D. WHY IT WAS FLAGGED (SCORING BREAKDOWN)
            ----------------------------------------- */}
        <div className="lg:col-span-5 bg-surface border border-line rounded-lg p-5 space-y-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-line pb-2">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-accent" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
                D. Why It Was Flagged (CIB Scoring Matrix)
              </h3>
            </div>
            <div className="font-mono text-sm">
              <strong className="text-base text-urgent">{campaign.score}</strong> / 100
            </div>
          </div>

          <div className="space-y-3">
            {Object.entries(campaign.features || {}).map(([key, points]) => {
              const feat = FEATURES[key] ?? { label: key, max: 25 }
              return (
                <div key={key} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-ink font-medium">{feat.label}</span>
                    <span className="font-mono text-muted">
                      {points} / {feat.max}
                    </span>
                  </div>
                  <ScoreBar value={points} max={feat.max} color={color} />
                </div>
              )
            })}

            <div className="pt-2 border-t border-line flex items-center justify-between text-xs font-mono font-bold">
              <span>Total Composite Score</span>
              <span className="text-urgent">{campaign.score} / 100</span>
            </div>
          </div>

          <div className="space-y-1.5 pt-1">
            <div className="text-[11px] text-muted uppercase tracking-wider">Identified Signals</div>
            <div className="flex flex-wrap gap-1.5">
              {campaign.signals?.map((s) => (
                <Badge key={s}>{SIGNALS[s] ?? s}</Badge>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* -----------------------------------------
          E. NETWORK / ACCOUNTS
          ----------------------------------------- */}
      <section className="bg-surface border border-line rounded-lg p-5 space-y-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-2">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-accent" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              E. Network &amp; Accounts ({fmt(campaign.size)} Coordinated Nodes)
            </h3>
          </div>
          <span className="text-xs text-muted">
            ACCOUNT → COORDINATION RELATIONSHIP → CAMPAIGN
          </span>
        </div>

        {/* Seeds and Amplifiers Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border border-line rounded-md overflow-hidden">
            <thead className="bg-subtle text-muted text-[11px] uppercase tracking-wider">
              <tr>
                <th className="py-2 px-3">Role</th>
                <th className="py-2 px-3">Handle</th>
                <th className="py-2 px-3">Platform</th>
                <th className="py-2 px-3">Account Age</th>
                <th className="py-2 px-3">First Seen</th>
                <th className="py-2 px-3">Location</th>
                <th className="py-2 px-3">Coordination Relationship</th>
                <th className="py-2 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {/* Seeds */}
              {campaign.seeds?.map((s) => (
                <tr key={s.account_id} className="hover:bg-subtle/50">
                  <td className="py-2 px-3">
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-urgent-soft text-urgent">
                      ORIGINATOR / SEED
                    </span>
                  </td>
                  <td className="py-2 px-3 font-mono font-medium text-ink">
                    @{s.username || s.account_id}
                  </td>
                  <td className="py-2 px-3">
                    {s.platform ? <PlatformChip platform={s.platform} /> : '—'}
                  </td>
                  <td className="py-2 px-3 font-mono">
                    {s.account_age_days != null ? (
                      <span className={s.account_age_days < 30 ? 'text-urgent font-bold' : 'text-muted'}>
                        {s.account_age_days} days
                      </span>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="py-2 px-3 font-mono text-muted">{fmtClock(s.first_seen)}</td>
                  <td className="py-2 px-3 text-muted">{s.city || '—'}</td>
                  <td className="py-2 px-3 text-muted truncate max-w-xs">{s.text || 'Initiating broadcast'}</td>
                  <td className="py-2 px-3 text-right">
                    <button
                      onClick={() => onFilter({ account: s.account_id })}
                      className="text-accent hover:underline cursor-pointer font-medium"
                    >
                      Posts →
                    </button>
                  </td>
                </tr>
              ))}

              {/* Amplifiers */}
              {campaign.amplifiers?.map((a) => (
                <tr key={a.account_id} className="hover:bg-subtle/50">
                  <td className="py-2 px-3">
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-accent/10 text-accent">
                      AMPLIFIER NODE
                    </span>
                  </td>
                  <td className="py-2 px-3 font-mono font-medium text-ink">
                    @{a.username || a.account_id}
                  </td>
                  <td className="py-2 px-3 text-muted">Multi-platform</td>
                  <td className="py-2 px-3 text-muted font-mono">—</td>
                  <td className="py-2 px-3 font-mono text-muted">—</td>
                  <td className="py-2 px-3 text-muted">—</td>
                  <td className="py-2 px-3 font-mono text-muted">
                    {a.links} cross-links · {a.posts} posts
                  </td>
                  <td className="py-2 px-3 text-right">
                    <button
                      onClick={() => onFilter({ account: a.account_id })}
                      className="text-accent hover:underline cursor-pointer font-medium"
                    >
                      Posts →
                    </button>
                  </td>
                </tr>
              ))}

              {/* General Accounts fallback */}
              {(!campaign.seeds || campaign.seeds.length === 0) &&
                campaign.accounts?.slice(0, 10).map((acc) => (
                  <tr key={acc} className="hover:bg-subtle/50">
                    <td className="py-2 px-3">
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-subtle text-muted">
                        PARTICIPANT
                      </span>
                    </td>
                    <td className="py-2 px-3 font-mono font-medium text-ink">@{acc}</td>
                    <td className="py-2 px-3 text-muted">Social</td>
                    <td className="py-2 px-3 text-muted">—</td>
                    <td className="py-2 px-3 text-muted">—</td>
                    <td className="py-2 px-3 text-muted">—</td>
                    <td className="py-2 px-3 text-muted">Coordinated cluster participant</td>
                    <td className="py-2 px-3 text-right">
                      <button
                        onClick={() => onFilter({ account: acc })}
                        className="text-accent hover:underline cursor-pointer font-medium"
                      >
                        Posts →
                      </button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* -----------------------------------------
          F. IBM BOB ASSESSMENT
          ----------------------------------------- */}
      <section className="bg-surface border border-line rounded-lg p-5 space-y-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-2">
          <div className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-accent" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              F. IBM Bob Semantic Threat Assessment
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">Status:</span>
            {verdict ? (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-benign">
                <CheckCircle2 className="w-3.5 h-3.5" /> Classified
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs text-alert font-medium">
                <Clock className="w-3.5 h-3.5" /> Pending Classification
              </span>
            )}
          </div>
        </div>

        {asking ? (
          <div className="p-8 flex flex-col items-center justify-center gap-3 text-muted">
            <Spinner className="w-5 h-5 text-accent" />
            <p className="text-xs">
              IBM Bob is analyzing coordination semantics, threat intent, and multilingual evidence (approx. 15–20s)…
            </p>
          </div>
        ) : verdict ? (
          <div className="space-y-4">
            {/* Top Verdict Strip */}
            <div className="flex flex-wrap items-center gap-3 p-3 rounded-md bg-subtle/60 border border-line">
              <LevelBadge level={escalation.level} />
              <div className="text-sm font-semibold text-ink">
                {THREATS[verdict.threat_type] || verdict.threat_type}
              </div>
              <span className="text-xs text-muted">
                · Severity <strong className="text-ink">{verdict.severity}</strong> of 5
              </span>
              <span className="ml-auto text-xs text-faint font-mono">
                {result.cached ? 'Saved Analysis' : `Cost ${result.cost?.toFixed(3)} Bobcoins`}
              </span>
            </div>

            {/* Offline Call to Action Banner if detected */}
            {event && (
              <div className="rounded-md bg-urgent-soft text-urgent p-3 border border-urgent/20 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider">
                  <AlertTriangle className="w-4 h-4" /> Physical Gathering Call Detected
                </div>
                <div className="text-xs font-semibold">
                  Location: {event.where} · Timing: {fmtDay(event.at)}, {fmtClock(event.at)}
                </div>
                <p className="text-xs opacity-90">
                  {event.what} (Posts state: “{event.where_quote}”)
                </p>
              </div>
            )}

            {/* Target and Narrative */}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="p-3 rounded-md border border-line bg-surface space-y-1">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">Target Entity</div>
                <div className="text-sm font-medium text-ink">{verdict.target || 'General Public'}</div>
              </div>
              <div className="p-3 rounded-md border border-line bg-surface space-y-1">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                  Operational Narrative
                </div>
                <p className="text-xs text-muted leading-relaxed">{verdict.narrative}</p>
              </div>
            </div>

            {/* Re-classify Button */}
            {bobConfigured && (
              <div className="flex justify-end">
                <Button onClick={askBob} variant="ghost" className="text-xs h-7">
                  <RefreshCw className="w-3.5 h-3.5" /> Re-classify with IBM Bob
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3 p-4 rounded-md bg-subtle/50 border border-line">
            <p className="text-xs text-muted leading-relaxed">
              This campaign has not been evaluated by IBM Bob yet. IBM Bob performs multilingual semantic inference
              across sample posts to identify targeted entities, threat narrative, offline mobilization risk, and
              applicable legal statutes.
            </p>
            <div className="flex items-center gap-3">
              <Button variant="primary" onClick={askBob} disabled={!bobConfigured}>
                <Bot className="w-4 h-4" /> Classify with IBM Bob
              </Button>
              {!bobConfigured && (
                <span className="text-xs text-muted">
                  (Live classification requires BOB_API_KEY and Bob Shell on PATH)
                </span>
              )}
            </div>
          </div>
        )}
      </section>

      {/* -----------------------------------------
          G. RECOMMENDED ACTIONS
          ----------------------------------------- */}
      <section className="bg-surface border border-line rounded-lg p-5 space-y-4 shadow-xs">
        <div className="flex items-center justify-between border-b border-line pb-2">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-accent" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              G. Recommended Actions &amp; Investigator Status Area
            </h3>
          </div>
          <span className="text-xs text-muted">Operational Workflow</span>
        </div>

        {/* 7-Step Status Workflow Chips */}
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-benign-soft text-benign font-medium">
            <Check className="w-3.5 h-3.5" /> Campaign detected
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-benign-soft text-benign font-medium">
            <Check className="w-3.5 h-3.5" /> Coordination analyzed
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-benign-soft text-benign font-medium">
            <Check className="w-3.5 h-3.5" /> Evidence collected
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-benign-soft text-benign font-medium">
            <Check className="w-3.5 h-3.5" /> SHA-256 hashes generated
          </span>
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md font-medium ${
              verdict ? 'bg-benign-soft text-benign' : 'bg-subtle text-muted'
            }`}
          >
            {verdict ? <Check className="w-3.5 h-3.5" /> : '○'} IBM Bob classification
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-subtle text-muted font-medium">
            ○ Investigator verification
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-subtle text-muted font-medium">
            ○ Formal escalation
          </span>
        </div>

        {/* Action Items List */}
        <div className="space-y-1.5 pt-2">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">
            Operational Directives:
          </div>
          <ul className="space-y-1 text-xs text-ink list-disc pl-5">
            {escalation?.actions?.length ? (
              escalation.actions.map((act, i) => <li key={i}>{act}</li>)
            ) : (
              <>
                <li>Trigger IBM Bob classification to establish narrative intent and threat level.</li>
                <li>Preserve cryptographic SHA-256 evidence records for potential Section 63 BSA submission.</li>
                <li>Cross-reference originator seed accounts with telecommunication subscriber registries.</li>
              </>
            )}
          </ul>
        </div>
      </section>

      {/* -----------------------------------------
          H. EVIDENCE RECORDS (SECTION 63 BSA CHAIN)
          ----------------------------------------- */}
      <section className="bg-surface border border-line rounded-lg p-5 space-y-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-2">
          <div className="flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-accent" />
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
                H. Evidence Records (Section 63 BSA Cryptographic Chain)
              </h3>
              <p className="text-[11px] text-muted">
                Authentic post captures hashed at ingestion with SHA-256
              </p>
            </div>
          </div>

          <Button
            onClick={() => setShowAllEvidence(!showAllEvidence)}
            className="cursor-pointer text-xs"
          >
            {showAllEvidence
              ? `Hide Evidence Table`
              : `View All Evidence (${samplePosts.length} Records)`}{' '}
            {showAllEvidence ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </Button>
        </div>

        {/* Top Sample Records View */}
        {!showAllEvidence && (
          <div className="space-y-2.5">
            <div className="text-xs text-muted">
              Displaying representative sample evidence. Click <strong>View All Evidence</strong> above to search and inspect all records.
            </div>
            <div className="grid gap-2.5 md:grid-cols-2">
              {samplePosts.slice(0, 4).map((p) => {
                const isCited = evidenceSet.has(p.post_id)
                const postHash = p.sha256_hash || p.sha256 || ''
                const isCopied = copiedHash === postHash
                return (
                  <div
                    key={p.post_id}
                    className={`rounded-md border p-3 text-xs space-y-2 transition-colors ${
                      isCited ? 'border-accent/50 bg-subtle/50' : 'border-line bg-surface'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 text-muted">
                      <div className="flex items-center gap-1.5 font-mono">
                        {p.platform && <PlatformChip platform={p.platform} />}
                        <span className="font-semibold text-ink">@{p.username || p.account_id}</span>
                      </div>
                      <span className="font-mono text-[11px]">{fmtClockSeconds(p.created_at)}</span>
                    </div>

                    <p className="text-ink leading-relaxed break-words">{p.text}</p>

                    <div className="pt-2 border-t border-line/60 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1 font-mono text-[10px] text-muted truncate max-w-[200px]">
                        <span>ID: {p.post_id}</span>
                        {isCited && <span className="text-accent font-sans font-bold">· Cited by Bob</span>}
                      </div>

                      {postHash && (
                        <button
                          onClick={() => onCopyHash(postHash)}
                          title="Click to copy full SHA-256 hash"
                          className="inline-flex items-center gap-1 font-mono text-[10px] px-1.5 py-0.5 rounded bg-subtle text-muted hover:text-ink hover:bg-subtle/80 cursor-pointer"
                        >
                          {isCopied ? <Check className="w-3 h-3 text-benign" /> : <Copy className="w-3 h-3" />}
                          <span>{postHash.slice(0, 10)}…</span>
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Full Expanded Evidence Table with Search, Filter, Sort, Expand */}
        {showAllEvidence && (
          <div className="space-y-3">
            {/* Search and Filters */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-subtle p-3 rounded-md">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  type="text"
                  placeholder="Filter by keyword, handle, post ID, or hash…"
                  value={evidenceSearch}
                  onChange={(e) => setEvidenceSearch(e.target.value)}
                  className="h-8 pl-8 pr-3 text-xs bg-surface border border-line rounded-md text-ink w-full focus:outline-accent"
                />
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={evidencePlatform}
                  onChange={(e) => setEvidencePlatform(e.target.value)}
                  className="h-8 px-2 text-xs bg-surface border border-line rounded-md text-ink cursor-pointer focus:outline-accent"
                >
                  <option value="all">Platform: All</option>
                  <option value="x">X (Twitter)</option>
                  <option value="telegram">Telegram</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="facebook">Facebook</option>
                </select>

                <select
                  value={evidenceSort}
                  onChange={(e) => setEvidenceSort(e.target.value)}
                  className="h-8 px-2 text-xs bg-surface border border-line rounded-md text-ink cursor-pointer focus:outline-accent"
                >
                  <option value="earliest">Sort: Earliest First</option>
                  <option value="latest">Sort: Latest First</option>
                </select>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto border border-line rounded-md">
              <table className="w-full text-left text-xs">
                <thead className="bg-subtle text-muted text-[11px] uppercase tracking-wider">
                  <tr>
                    <th className="py-2 px-3">Post ID</th>
                    <th className="py-2 px-3">Time ({zoneLabel()})</th>
                    <th className="py-2 px-3">Handle / Platform</th>
                    <th className="py-2 px-3">Content Text</th>
                    <th className="py-2 px-3">SHA-256 Digest</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {filteredEvidence.map((p) => {
                    const isExpanded = expandedPostIds.has(p.post_id)
                    const postHash = p.sha256_hash || p.sha256 || ''
                    const isCopied = copiedHash === postHash
                    const isCited = evidenceSet.has(p.post_id)

                    return (
                      <tr
                        key={p.post_id}
                        className={`hover:bg-subtle/50 ${isCited ? 'bg-accent/5' : ''}`}
                      >
                        <td className="py-2.5 px-3 font-mono font-medium text-ink align-top">
                          <div className="flex flex-col gap-0.5">
                            <span>{p.post_id}</span>
                            {isCited && (
                              <span className="text-[10px] font-sans font-bold text-accent">
                                Cited by Bob
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-muted whitespace-nowrap align-top">
                          {fmtClockSeconds(p.created_at)}
                        </td>
                        <td className="py-2.5 px-3 align-top whitespace-nowrap">
                          <div className="flex items-center gap-1.5 font-mono">
                            {p.platform && <PlatformChip platform={p.platform} />}
                            <span className="font-semibold text-ink">
                              @{p.username || p.account_id}
                            </span>
                          </div>
                        </td>
                        <td className="py-2.5 px-3 align-top">
                          <p
                            className={`leading-relaxed text-ink break-words ${
                              isExpanded ? '' : 'line-clamp-2'
                            }`}
                          >
                            {p.text}
                          </p>
                          {p.text?.length > 120 && (
                            <button
                              onClick={() => toggleExpandPost(p.post_id)}
                              className="text-[11px] text-accent hover:underline cursor-pointer font-medium mt-1"
                            >
                              {isExpanded ? 'Show less' : 'Show full text'}
                            </button>
                          )}
                        </td>
                        <td className="py-2.5 px-3 align-top">
                          {postHash ? (
                            <div className="flex items-center gap-1.5">
                              <span
                                className="font-mono text-[10px] text-muted truncate max-w-[140px]"
                                title={postHash}
                              >
                                {postHash}
                              </span>
                              <button
                                onClick={() => onCopyHash(postHash)}
                                title="Copy 64-character SHA-256 hash"
                                className="p-1 rounded bg-subtle hover:bg-subtle/80 text-muted hover:text-ink cursor-pointer"
                              >
                                {isCopied ? (
                                  <Check className="w-3.5 h-3.5 text-benign" />
                                ) : (
                                  <Copy className="w-3.5 h-3.5" />
                                )}
                              </button>
                            </div>
                          ) : (
                            <span className="text-faint text-[10px] font-mono">—</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* -----------------------------------------
          I. LEGAL & OPERATIONAL NOTES (SECTION 63 BSA)
          ----------------------------------------- */}
      <section className="bg-surface border border-line rounded-lg p-5 space-y-4 shadow-xs">
        <div className="flex items-center justify-between border-b border-line pb-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-accent" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              I. Statutory Provisions &amp; Section 63 BSA Notice
            </h3>
          </div>
          <span className="text-xs text-alert font-medium">Verify with Legal Officer</span>
        </div>

        {/* Legal Suggestions */}
        {verdict?.legal_suggestions?.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-medium text-muted">
              Suggested Statutory Sections (Bharatiya Nyaya Sanhita &amp; IT Act):
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {verdict.legal_suggestions.map((s) => (
                <div key={s.id} className="p-3 rounded-md bg-subtle/70 border border-line text-xs space-y-1">
                  <div className="font-bold text-ink">
                    {s.law}{' '}
                    <span className="font-normal text-muted">
                      {s.ipc && s.ipc !== '—' && `(formerly ${s.ipc}) · `}
                      {s.title}
                    </span>
                  </div>
                  <p className="text-muted leading-relaxed">{s.why}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Section 63 BSA Limitations & Human Review Notice */}
        <div className="rounded-md border border-line bg-subtle/40 p-4 text-xs space-y-2 text-muted leading-relaxed">
          <div className="font-bold text-ink uppercase tracking-wide text-[11px]">
            Section 63 Bharatiya Sakshya Adhiniyam, 2023 (BSA) Evidentiary Notice
          </div>
          <p>
            <strong>Automated Decision Support:</strong> Heuristic CIB scores and IBM Bob semantic classifications
            are algorithmic decision-support outputs. They do not constitute automated determinations of criminal
            liability, conspiracy, or intent.
          </p>
          <p>
            <strong>Cryptographic Integrity vs Chain of Custody:</strong> The SHA-256 hashes generated for each
            post verify cryptographic data integrity from the moment of ingestion into this system. However,
            under Section 63 of the BSA (replacing Section 65B of the Indian Evidence Act), cryptographic hashing
            alone does not substitute for an officer-signed Certificate of Electronic Record, lawful interception
            records, or platform-verified chain of custody.
          </p>
          <p>
            <strong>Mandatory Human Verification:</strong> Investigating officers must independently review original
            posts, subscriber identifiers, and corroborating contextual telemetry before initiating statutory
            takedown notices or formal First Information Reports (FIR).
          </p>
        </div>
      </section>
    </div>
  )
}
