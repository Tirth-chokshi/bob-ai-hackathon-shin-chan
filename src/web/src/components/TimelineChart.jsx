import React from 'react'
import { campaignColor, fmt, fmtTime, BUCKET_LABEL } from '../labels'

const W = 1000
const H = 180

// Posts per bucket: all posts as a grey area, each campaign's accounts as a coloured line
export function TimelineChart({ timeline }) {
  const { points, bucket_seconds, campaign_ids } = timeline
  if (!points.length) return <p className="text-sm text-muted">No posts in this dataset.</p>

  const max = Math.max(1, ...points.map((p) => p.total))
  const x = (i) => (points.length === 1 ? W / 2 : (i / (points.length - 1)) * W)
  const y = (v) => H - (v / max) * (H - 6)
  const line = (key) => points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p[key] || 0).toFixed(1)}`).join('')
  const withYear = points.at(-1).t - points[0].t > 300 * 86400
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => points[Math.round(f * (points.length - 1))])

  return (
    <figure>
      <div className="flex justify-between text-xs text-faint font-mono mb-1">
        <span>{fmt(max)} posts per {BUCKET_LABEL[bucket_seconds] ?? `${bucket_seconds} s`}</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="block w-full h-44" role="img"
        aria-label={`Posts per ${BUCKET_LABEL[bucket_seconds]}, peak ${max}`}>
        <path d={`${line('total')}L${W},${H}L0,${H}Z`} fill="var(--line)" />
        {campaign_ids.map((id) => (
          <path key={id} d={line(id)} fill="none" stroke={campaignColor(id)} strokeWidth="1.75" vectorEffect="non-scaling-stroke" />
        ))}
        <line x1="0" x2={W} y1={H - 0.5} y2={H - 0.5} stroke="var(--line)" vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="flex justify-between text-xs text-faint font-mono mt-1">
        {ticks.map((p, i) => <span key={i}>{fmtTime(p.t, withYear)}</span>)}
      </div>
      <figcaption className="flex flex-wrap gap-x-4 gap-y-1 mt-3 text-xs text-muted">
        <span className="flex items-center gap-1.5"><span className="w-3 h-2 rounded-sm bg-line" />All posts</span>
        {campaign_ids.map((id) => (
          <span key={id} className="flex items-center gap-1.5">
            <span className="w-3 h-0.5" style={{ background: campaignColor(id) }} />{id.toUpperCase()}
          </span>
        ))}
      </figcaption>
    </figure>
  )
}
