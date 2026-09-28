import React from 'react'
import { Clock, Flag, MapPin, Radar } from 'lucide-react'
import { LevelBadge } from '../ui'
import { PlatformChips } from './Chips'
import { campaignColor, fmt, fmtClock, fmtDay, fmtGap, THREATS } from '../labels'

// The hero of the Overview: every planned offline gathering IBM Bob found, soonest first.
// Falls back to showing URGENT/ALERT campaigns when no offline events exist.
export function ThreatCards({ campaigns, batchEnd, selectedId, onSelect }) {
  const threats = campaigns
    .filter((c) => c.assessment?.offline_event?.at)
    .sort((a, b) => a.assessment.offline_event.at - b.assessment.offline_event.at)

  // If no offline events, show URGENT/ALERT campaigns instead
  if (threats.length === 0) {
    const urgent = campaigns.filter((c) => c.assessment?.level === 'URGENT')
    const alert = campaigns.filter((c) => c.assessment?.level === 'ALERT')
    const flagged = [...urgent, ...alert]

    if (flagged.length === 0) return null  // the Summary above already says so

    return (
      <section aria-label="High-priority campaigns" className="space-y-2">
        <h2 className="flex items-center gap-1.5 text-xs font-semibold tracking-wide uppercase text-urgent">
          <Flag className="w-3.5 h-3.5" aria-hidden /> High-priority campaigns
        </h2>
        <div className={`grid gap-3 ${flagged.length > 1 ? 'lg:grid-cols-2' : ''}`}>
          {flagged.map((c) => (
            <button key={c.id} onClick={() => onSelect(c.id)} aria-pressed={c.id === selectedId}
              className={`text-left w-full rounded-lg border bg-surface p-4 cursor-pointer transition-shadow ${c.id === selectedId ? 'border-line shadow-md' : 'border-line hover:shadow-sm'}`}
              style={{ borderLeftWidth: 4, borderLeftColor: `var(--${c.assessment.level.toLowerCase()})` }}>
              <div className="flex flex-wrap items-center gap-2">
                <LevelBadge level={c.assessment.level} />
                <span className="text-sm font-medium">{THREATS[c.assessment.threat_type] ?? c.assessment.threat_type}</span>
                <span className="text-xs text-muted">· severity {c.assessment.severity}/5</span>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: campaignColor(c.id) }} />
                <span><strong className="text-ink font-mono">{c.id.toUpperCase()}</strong> {c.top_hashtag}</span>
                <span>· {fmt(c.size)} accounts · score {c.score}/100</span>
              </div>
            </button>
          ))}
        </div>
      </section>
    )
  }

  return (
    <section aria-label="Emerging offline threats" className="space-y-2">
      <h2 className="flex items-center gap-1.5 text-xs font-semibold tracking-wide uppercase text-urgent">
        <Flag className="w-3.5 h-3.5" aria-hidden /> Emerging offline threats
      </h2>
      <div className={`grid gap-3 ${threats.length > 1 ? 'lg:grid-cols-2' : ''}`}>
        {threats.map((c) => (
          <ThreatCard key={c.id} c={c} batchEnd={batchEnd} selected={c.id === selectedId} onSelect={onSelect} />
        ))}
      </div>
    </section>
  )
}

function ThreatCard({ c, batchEnd, selected, onSelect }) {
  const { level, offline_event: ev } = c.assessment
  const lead = c.detected_at ? ev.at - c.detected_at : null
  const left = ev.at - batchEnd

  return (
    <button onClick={() => onSelect(c.id)} aria-pressed={selected}
      className={`text-left w-full rounded-lg border bg-surface p-4 border-l-4 cursor-pointer transition-shadow ${selected ? 'border-line shadow-md' : 'border-line hover:shadow-sm'}`}
      style={{ borderLeftColor: `var(--${level.toLowerCase()})` }}>
      <div className="flex flex-wrap items-center gap-2">
        <LevelBadge level={level} />
        <span className="text-sm font-medium">{ev.what}</span>
      </div>

      <div className="mt-3 flex flex-wrap items-end gap-x-8 gap-y-3">
        <div className="min-w-0">
          <div className="flex items-center gap-1 text-xs text-muted"><MapPin className="w-3.5 h-3.5" aria-hidden />Where</div>
          <div className="text-2xl font-semibold leading-tight">{ev.where}</div>
          <div className="text-xs text-faint truncate" title="As written in the posts">"{ev.where_quote}"</div>
        </div>
        <div>
          <div className="flex items-center gap-1 text-xs text-muted"><Clock className="w-3.5 h-3.5" aria-hidden />When</div>
          <div className="text-2xl font-semibold font-mono leading-tight">{fmtClock(ev.at)}</div>
          <div className="text-xs text-muted">{fmtDay(ev.at)}</div>
        </div>
        {left > 0 && (
          <div className="ml-auto text-right">
            <div className="text-xs text-muted">Time left after the last post</div>
            <div className="text-2xl font-semibold font-mono leading-tight text-urgent">{fmtGap(left)}</div>
          </div>
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
        <span className="w-2.5 h-2.5 rounded-full" style={{ background: campaignColor(c.id) }} />
        <span>Called by <strong className="text-ink font-mono">{c.id.toUpperCase()}</strong> {c.top_hashtag}</span>
        <span>· {fmt(c.size)} accounts ·</span>
        {c.platform_path && <PlatformChips names={c.platform_path.map((p) => p.name)} />}
        {c.town_path && <span>· {c.town_path.length} towns</span>}
      </div>

      {lead > 0 && (
        <div className="mt-3 flex items-center gap-2 rounded-md bg-benign-soft text-benign px-3 py-2 text-sm">
          <Radar className="w-4 h-4 shrink-0" aria-hidden />
          <span>Flagged at <strong className="font-mono">{fmtClock(c.detected_at)}</strong>, <strong>{fmtGap(lead)} before</strong> the gathering</span>
        </div>
      )}
    </button>
  )
}
