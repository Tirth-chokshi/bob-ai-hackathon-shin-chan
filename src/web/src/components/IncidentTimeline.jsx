import React from 'react'
import { campaignColor, fmt, fmtClock, fmtDate, fmtDay, fmtGap, fmtWhen, zoneLabel, zoneOffset, BUCKET_LABEL, NICE_BUCKETS } from '../labels'

const W = 1000
const H = 160
const MAX_COLUMNS = 160

// One picture of the incident: activity waves per campaign, and for the selected campaign when it started,
// when we could flag it, when it peaked and when the crowd is called, with the lead time between.
export function IncidentTimeline({ timeline, campaigns, selectedId }) {
  const { points, bucket_seconds, campaign_ids } = timeline
  if (!points.length) return <p className="text-sm text-muted">No posts in this dataset.</p>

  // Merge buckets into a size a person would pick (5 minutes, an hour, a day…) so bursts read as waves, not
  // hairlines, and line the columns up with the dataset's local hours and days
  const span = points.at(-1).t + bucket_seconds - points[0].t
  const bucket = NICE_BUCKETS.find((b) => b >= bucket_seconds && b % bucket_seconds === 0 && span / b <= MAX_COLUMNS)
    ?? bucket_seconds * Math.ceil(points.length / MAX_COLUMNS)
  const offset = zoneOffset(points[0].t)
  const colStart = (t) => Math.floor((t + offset) / bucket) * bucket - offset
  const byStart = new Map()
  for (const p of points) {
    const t = colStart(p.t)
    if (!byStart.has(t)) byStart.set(t, { t, total: 0, ...Object.fromEntries(campaign_ids.map((id) => [id, 0])) })
    const col = byStart.get(t)
    col.total += p.total
    for (const id of campaign_ids) col[id] += p[id] || 0
  }
  const cols = [...byStart.values()]

  const focus = campaigns.find((c) => c.id === selectedId)
  const event = focus?.assessment?.offline_event
  const start = cols[0].t
  const dataEnd = cols.at(-1).t + bucket
  const end = Math.max(dataEnd, event?.at ? event.at + (event.at - start) * 0.05 : 0)  // room for the gathering
  const pct = (t) => ((t - start) / (end - start)) * 100
  const X = (t) => (pct(t) / 100) * W
  const max = Math.max(1, ...cols.map((c) => c.total))
  const Y = (v) => H - (v / max) * (H - 6)

  // Stacked layers: campaigns bottom-up in rank order, everyday posts on top
  const layers = [...campaign_ids.map((id) => ({ id, value: (c) => c[id] })),
    { id: 'rest', value: (c) => c.total - campaign_ids.reduce((s, id) => s + c[id], 0) }]
  const base = cols.map(() => 0)
  const paths = layers.map((layer) => {
    const lower = [...base]
    cols.forEach((c, i) => { base[i] += layer.value(c) })
    let d = ''
    cols.forEach((c, i) => { d += `${i ? 'L' : 'M'}${X(c.t)},${Y(base[i])}L${X(c.t + bucket)},${Y(base[i])}` })
    for (let i = cols.length - 1; i >= 0; i--) d += `L${X(cols[i].t + bucket)},${Y(lower[i])}L${X(cols[i].t)},${Y(lower[i])}`
    return { id: layer.id, d: d + 'Z' }
  })

  // Markers for the selected campaign
  const peakCol = focus && cols.reduce((best, c) => ((c[focus.id] || 0) > (best[focus.id] || 0) ? c : best), cols[0])
  const markers = focus ? [
    focus.first_seen && { t: focus.first_seen, symbol: '●', label: 'first post', color: campaignColor(focus.id) },
    focus.detected_at && { t: focus.detected_at, symbol: '▲', label: 'flagged', color: 'var(--benign)' },
    peakCol && (peakCol[focus.id] || 0) > 0 && { t: peakCol.t + bucket / 2, symbol: '■', label: `peak ${fmt(peakCol[focus.id])} posts`, color: campaignColor(focus.id) },
    event?.at && { t: event.at, symbol: '⚑', label: 'gathering', color: 'var(--urgent)' },
  ].filter(Boolean).sort((a, b) => a.t - b.t) : []
  // Put each label in the first row where it doesn't overlap the previous one (labels are ~14% wide)
  const rowEnds = [-100, -100, -100]
  for (const m of markers) {
    const row = rowEnds.findIndex((end) => pct(m.t) - 7 > end + 1)
    m.row = row === -1 ? rowEnds.indexOf(Math.min(...rowEnds)) : row
    rowEnds[m.row] = pct(m.t) + 7
  }
  const lead = focus?.detected_at && event?.at ? event.at - focus.detected_at : null
  // Ticks on round local times: every 1/3/6/12 hours, or every 1/2/7/30 days, about five across
  const step = [3600, 3 * 3600, 6 * 3600, 12 * 3600, 86400, 2 * 86400, 7 * 86400, 30 * 86400, 91 * 86400, 365 * 86400]
    .find((st) => (end - start) / st <= 6) ?? 365 * 86400
  const ticks = []
  for (let t = Math.ceil((start + offset) / step) * step - offset; t <= end; t += step) ticks.push(t)
  const tickLabel = (t) => {
    if (step >= 86400) return fmtDate(t, step >= 30 * 86400)
    const midnight = (t + offset) % 86400 === 0
    return midnight && end - start > 20 * 3600 ? fmtDate(t, false) : fmtClock(t)
  }

  return (
    <figure>
      {/* marker labels, in two rows so close markers don't collide */}
      {markers.length > 0 && (
        <div className={`relative text-[11px] font-medium ${markers.some((m) => m.row === 2) ? 'h-16' : markers.length > 0 ? 'h-11' : 'h-0'}`}>
          {markers.map((m) => (
            <span key={m.label} title={`${m.label}: ${fmtDay(m.t)} ${fmtClock(m.t)} ${zoneLabel()}`}
              className={`absolute whitespace-nowrap px-1.5 py-0.5 rounded bg-surface border border-line ${pct(m.t) < 7 ? '' : pct(m.t) > 93 ? '-translate-x-full' : '-translate-x-1/2'}`}
              style={{ left: `${pct(m.t)}%`, top: m.row * 22, color: m.color }}>
              {m.symbol} {fmtWhen(m.t, end - start)} <span className="text-muted font-normal">{m.label}</span>
            </span>
          ))}
        </div>
      )}

      <div className="relative">
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="block w-full h-40" role="img"
          aria-label={`Posts per ${BUCKET_LABEL[bucket] ?? `${bucket / 60} minutes`}, stacked by campaign`}>
          {dataEnd < end && (
            <rect x={X(dataEnd)} y="0" width={W - X(dataEnd)} height={H} fill="var(--subtle)" opacity="0.7" />
          )}
          {paths.map((p) => (
            <path key={p.id} d={p.d}
              fill={p.id === 'rest' ? 'var(--line)' : campaignColor(p.id)}
              opacity={p.id === 'rest' ? 1 : !focus || p.id === focus.id ? 0.9 : 0.3} />
          ))}
          <line x1="0" x2={W} y1={H - 0.5} y2={H - 0.5} stroke="var(--line)" vectorEffect="non-scaling-stroke" />
        </svg>
        {/* marker lines */}
        {markers.map((m) => (
          <span key={m.label} className="absolute top-0 bottom-0 border-l-2 border-dashed pointer-events-none"
            style={{ left: `${pct(m.t)}%`, borderColor: m.color }} />
        ))}
        {dataEnd < end && (
          <span className="absolute top-1 text-[11px] text-muted pl-1.5" style={{ left: `${pct(dataEnd)}%` }}>after the last post</span>
        )}
        <span className="absolute left-1 top-1 text-[11px] text-faint">Busiest {BUCKET_LABEL[bucket] ?? fmtGap(bucket)}: {fmt(max)} posts · times in {zoneLabel()}</span>
      </div>

      <div className="relative h-5 mt-1 text-[11px] text-faint font-mono">
        {ticks.map((t) => (
          <span key={t} className={`absolute whitespace-nowrap ${pct(t) < 4 ? '' : pct(t) > 96 ? '-translate-x-full' : '-translate-x-1/2'}`}
            style={{ left: `${pct(t)}%` }}>
            {tickLabel(t)}
          </span>
        ))}
      </div>

      {lead > 0 && (
        <div className="relative h-8 mt-1">
          <div className="absolute top-1.5 h-3 border-x-2 border-b-2 rounded-b border-benign"
            style={{ left: `${pct(focus.detected_at)}%`, width: `${pct(event.at) - pct(focus.detected_at)}%` }} />
          <span className="absolute top-3 -translate-x-1/2 px-2 bg-surface text-xs font-semibold text-benign whitespace-nowrap"
            style={{ left: `${(pct(focus.detected_at) + pct(event.at)) / 2}%` }}>
            flagged {fmtGap(lead)} before the gathering
          </span>
        </div>
      )}

      <figcaption className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-muted">
        {campaign_ids.map((id) => (
          <span key={id} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm" style={{ background: campaignColor(id) }} />{id.toUpperCase()}
          </span>
        ))}
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-line" />Everyday posts</span>
      </figcaption>
    </figure>
  )
}
