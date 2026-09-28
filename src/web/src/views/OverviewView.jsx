import React from 'react'
import { Card, LevelBadge, ScoreBar } from '../ui'
import { Summary } from '../components/Summary'
import { ThreatCards } from '../components/ThreatCards'
import { IncidentTimeline } from '../components/IncidentTimeline'
import { SpreadMap } from '../components/SpreadMap'
import { LangChips, PlatformChips } from '../components/Chips'
import { campaignColor, fmt, SIGNALS, THREATS } from '../labels'

// Triage: one paragraph on what was found → planned gatherings → the incident on one timeline →
// campaigns with the selected campaign's detail beside them. Sections without data in this dataset are left out.
export function OverviewView({ dataset, data, selectedId, onSelect, panel }) {
  const { campaigns, timeline, stats } = data
  const batchEnd = timeline.points.length ? timeline.points.at(-1).t + timeline.bucket_seconds : 0
  const selected = campaigns.find((c) => c.id === selectedId)
  const hasPlatforms = campaigns.some((c) => c.platform_path?.length > 1)
  const hasTowns = campaigns.some((c) => c.town_path?.length)

  return (
    <div className="space-y-4">
      <Summary stats={stats} campaigns={campaigns} />
      <ThreatCards campaigns={campaigns} batchEnd={batchEnd} selectedId={selectedId} onSelect={onSelect} />

      <Card title="Incident timeline"
        subtitle="Posts over time, stacked by campaign. Click a campaign in the table below to highlight it.">
        <IncidentTimeline timeline={timeline} campaigns={campaigns} selectedId={selectedId} />
      </Card>

      <div className="grid gap-4 lg:grid-cols-12 items-start">
        <div className="lg:col-span-7 space-y-4">
          <Card title="Campaigns" subtitle="Ranked by coordination score. Select one to see the detail."
            bodyClassName="overflow-x-auto">
            {campaigns.length === 0 ? (
              <p className="p-6 text-sm text-muted text-center">
                No coordinated campaigns found: no group of 5 or more accounts repeatedly posted the same text, link or reply
                within seconds of each other.
              </p>
            ) : (
              <CampaignTable campaigns={campaigns} timeline={timeline} selectedId={selectedId} onSelect={onSelect} hasPlatforms={hasPlatforms} hasTowns={hasTowns} />
            )}
          </Card>
          {selected?.town_path?.length > 0 && (
            <Card title="Where it spread" subtitle={`${selected.id.toUpperCase()} reached these towns in the order numbered.`}>
              <SpreadMap towns={dataset.towns} campaign={selected} />
            </Card>
          )}
        </div>
        <div className="lg:col-span-5 lg:sticky lg:top-[72px] lg:max-h-[calc(100vh-88px)] lg:overflow-y-auto">
          {panel}
        </div>
      </div>
    </div>
  )
}

// Tiny activity curve for one campaign, from the dataset timeline
function Sparkline({ timeline, id }) {
  const pts = timeline.points
  const n = 48
  const size = Math.max(1, Math.ceil(pts.length / n))
  const cols = []
  for (let i = 0; i < pts.length; i += size) cols.push(pts.slice(i, i + size).reduce((s, p) => s + (p[id] || 0), 0))
  const max = Math.max(1, ...cols)
  const d = cols.map((v, i) => `${i ? 'L' : 'M'}${(i / Math.max(1, cols.length - 1)) * 100},${22 - (v / max) * 20}`).join('')
  return (
    <svg viewBox="0 0 100 24" preserveAspectRatio="none" className="w-24 h-6" aria-hidden>
      <path d={`${d}L100,24L0,24Z`} fill={campaignColor(id)} opacity="0.25" />
      <path d={d} fill="none" stroke={campaignColor(id)} strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

function CampaignTable({ campaigns, timeline, selectedId, onSelect, hasPlatforms, hasTowns }) {
  return (
    <table className="w-full text-sm">
      <thead className="bg-subtle text-xs text-muted text-left">
        <tr>
          <th className="font-medium px-4 py-2">Campaign</th>
          <th className="font-medium px-2 py-2">Activity</th>
          <th className="font-medium px-2 py-2 text-right">Accounts</th>
          <th className="font-medium px-2 py-2 w-28">Score</th>
          <th className="font-medium px-4 py-2">IBM Bob</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {campaigns.map((c) => {
          const selected = c.id === selectedId
          return (
            <tr key={c.id} onClick={() => onSelect(c.id)} aria-selected={selected}
              className={`cursor-pointer align-top ${selected ? 'bg-subtle' : 'hover:bg-subtle/60'}`}>
              <td className="px-4 py-3" style={{ boxShadow: selected ? `inset 3px 0 0 ${campaignColor(c.id)}` : undefined }}>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: campaignColor(c.id) }} />
                  <span className="font-medium font-mono">{c.id.toUpperCase()}</span>
                  <span className="text-muted truncate max-w-[180px]">{c.top_hashtag}</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-1.5 pl-4.5">
                  {hasPlatforms && c.platform_path && <PlatformChips names={c.platform_path.map((p) => p.name)} />}
                  {c.languages && <LangChips languages={c.languages} />}
                  {!hasPlatforms && c.signals?.map((s) => (
                    <span key={s} className="inline-flex items-center h-5 px-1.5 rounded bg-subtle text-[11px] text-muted">{SIGNALS[s] ?? s}</span>
                  ))}
                </div>
              </td>
              <td className="px-2 py-3"><Sparkline timeline={timeline} id={c.id} /></td>
              <td className="px-2 py-3 text-right font-mono tabular-nums">
                {fmt(c.size)}
                {hasTowns && c.town_path
                  ? <div className="text-[11px] text-muted font-sans">{c.town_path.length} towns</div>
                  : <div className="text-[11px] text-muted font-sans">{fmt(c.post_count)} posts</div>
                }
              </td>
              <td className="px-2 py-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono tabular-nums w-6 text-right">{c.score}</span>
                  <ScoreBar value={c.score} color={campaignColor(c.id)} />
                </div>
              </td>
              <td className="px-4 py-3">
                <LevelBadge level={c.assessment?.level} />
                {c.assessment && <div className="text-muted text-xs mt-1">{THREATS[c.assessment.threat_type]}</div>}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
