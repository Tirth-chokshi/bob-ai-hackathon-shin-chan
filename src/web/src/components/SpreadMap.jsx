import React from 'react'
import { campaignColor, fmtClock } from '../labels'

// Stylised map: towns as dots (placed from the dataset's coordinates if it has them, else in a ring), the selected campaign's towns numbered in the order it reached
// them, arrows between them, and a flag where the crowd is called. Towns without map coordinates
// (uploaded data) are laid out on a circle.
export function SpreadMap({ towns, campaign }) {
  const path = campaign?.town_path ?? []
  if (!path.length) return <p className="text-sm text-muted">No town information in this dataset.</p>

  const names = towns ? Object.keys(towns) : path.map((t) => t.name)
  const pos = {}
  names.forEach((n, i) => {
    const angle = (i / names.length) * 2 * Math.PI - Math.PI / 2
    pos[n] = towns?.[n] ?? [50 + 36 * Math.cos(angle), 50 + 36 * Math.sin(angle)]
  })
  const P = (n) => [pos[n][0], pos[n][1] * 0.46 + 7]  // map space is 100 × 60 (wide, like a district strip)
  const color = campaignColor(campaign.id)
  const maxPosts = Math.max(...path.map((t) => t.posts))
  const reached = Object.fromEntries(path.map((t, i) => [t.name, { ...t, order: i + 1 }]))
  const event = campaign.assessment?.offline_event
  const eventTown = event && names.find((n) => `${event.where} ${event.where_quote}`.toLowerCase().includes(n.toLowerCase()))

  return (
    <svg viewBox="0 0 100 60" className="block w-full max-h-[360px]" role="img"
      aria-label={`${campaign.id} reached ${path.map((t) => t.name).join(', then ')}`}>
      <defs>
        <marker id={`arrow-${campaign.id}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill={color} />
        </marker>
      </defs>
      <rect x="1" y="1" width="98" height="58" rx="4" fill="var(--subtle)" stroke="var(--line)" strokeWidth="0.3" />

      {/* faint roads between all towns */}
      {names.flatMap((a, i) => names.slice(i + 1).map((b) => (
        <line key={`${a}-${b}`} x1={P(a)[0]} y1={P(a)[1]} x2={P(b)[0]} y2={P(b)[1]} stroke="var(--line)" strokeWidth="0.25" />
      )))}

      {/* hops in order, curved so they don't hide the roads */}
      {path.slice(1).map((t, i) => {
        const [x1, y1] = P(path[i].name)
        const [x2, y2] = P(t.name)
        const mx = (x1 + x2) / 2 - (y2 - y1) * 0.18
        const my = (y1 + y2) / 2 + (x2 - x1) * 0.18
        return <path key={t.name} d={`M${x1},${y1} Q${mx},${my} ${x2},${y2}`} fill="none" stroke={color}
          strokeWidth="0.6" markerEnd={`url(#arrow-${campaign.id})`} opacity="0.85" />
      })}

      {names.map((n) => {
        const [x, y] = P(n)
        const r = reached[n]
        return (
          <g key={n}>
            {r && <circle cx={x} cy={y} r={2 + 3.5 * Math.sqrt(r.posts / maxPosts)} fill={color} opacity="0.18" />}
            <circle cx={x} cy={y} r={r ? 1.9 : 1} fill={r ? color : 'var(--faint)'} />
            {r && <text x={x} y={y + 0.75} textAnchor="middle" fontSize="2.1" fontWeight="700" fill="#fff">{r.order}</text>}
            <text x={x} y={y + (r ? 5.6 : 3.6)} textAnchor="middle" fontSize="2.3" fontWeight="600" fill="var(--ink)">{n}</text>
            {r && <text x={x} y={y + 8.2} textAnchor="middle" fontSize="1.8" fill="var(--muted)">{fmtClock(r.first_seen)} · {r.posts} posts</text>}
          </g>
        )
      })}

      {eventTown && (() => {
        const [x, y] = P(eventTown)
        return (
          <g>
            <line x1={x + 1.8} y1={y - 1} x2={x + 1.8} y2={y - 6} stroke="var(--urgent)" strokeWidth="0.4" />
            <path d={`M${x + 1.8},${y - 6} L${x + 5.4},${y - 5.1} L${x + 1.8},${y - 4.2} z`} fill="var(--urgent)" />
            <text x={x} y={y + 10.8} textAnchor="middle" fontSize="1.9" fontWeight="700" fill="var(--urgent)">gathering {fmtClock(event.at)}</text>
          </g>
        )
      })()}
    </svg>
  )
}
