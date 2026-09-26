import React, { useState } from 'react'

const CAMPAIGN_COLORS = {
  c1: '#8b5cf6', // Violet
  c2: '#ec4899', // Pink
  c3: '#f59e0b', // Amber
  c4: '#10b981', // Emerald
  c5: '#06b6d4', // Cyan
}

export function TimelineChart({ timelineData }) {
  const [hoveredPoint, setHoveredPoint] = useState(null)

  if (!timelineData || !timelineData.points || timelineData.points.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/40 rounded-xl border border-slate-800 text-slate-500 text-sm">
        No temporal activity points available.
      </div>
    )
  }

  const { points, campaign_ids = [] } = timelineData
  // Sample points if too dense for smooth SVG rendering (e.g. max 120 points)
  const step = Math.max(1, Math.floor(points.length / 120))
  const sampledPoints = points.filter((_, idx) => idx % step === 0)

  const maxTotal = Math.max(...sampledPoints.map((p) => p.total || 0), 10)
  const width = 800
  const height = 180
  const padding = 20

  const getX = (index) => padding + (index / (sampledPoints.length - 1)) * (width - 2 * padding)
  const getY = (val) => height - padding - (val / maxTotal) * (height - 2 * padding)

  // Generate path data for total volume
  const totalPathData = sampledPoints.reduce((acc, pt, idx) => {
    const x = getX(idx)
    const y = getY(pt.total || 0)
    return `${acc} ${idx === 0 ? 'M' : 'L'} ${x} ${y}`
  }, '')

  const totalArea = `${totalPathData} L ${getX(sampledPoints.length - 1)} ${height - padding} L ${getX(0)} ${height - padding} Z`

  return (
    <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="font-bold text-white text-sm">Activity Bursts & Temporal Synchronization</h3>
          <p className="text-xs text-slate-400">
            Posts per 60-second window across full dataset and coordinated campaign clusters
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-slate-400 font-mono">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-600"></span>
            Total Stream
          </div>
          {campaign_ids.map((cid) => (
            <div key={cid} className="flex items-center gap-1.5 font-mono text-slate-300">
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: CAMPAIGN_COLORS[cid] || '#6366f1' }}
              ></span>
              Campaign {cid.toUpperCase()}
            </div>
          ))}
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative overflow-hidden w-full">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-44 overflow-visible select-none"
        >
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = height - padding - pct * (height - 2 * padding)
            return (
              <g key={i}>
                <line
                  x1={padding}
                  y1={y}
                  x2={width - padding}
                  y2={y}
                  stroke="#1e293b"
                  strokeDasharray="3 3"
                />
                <text
                  x={padding - 4}
                  y={y + 3}
                  fill="#475569"
                  fontSize="9"
                  textAnchor="end"
                  fontFamily="monospace"
                >
                  {Math.round(pct * maxTotal)}
                </text>
              </g>
            )
          })}

          {/* Total volume area & line */}
          <path d={totalArea} fill="#334155" fillOpacity="0.25" />
          <path d={totalPathData} fill="none" stroke="#475569" strokeWidth="1.5" />

          {/* Individual campaign curves */}
          {campaign_ids.map((cid) => {
            const campPath = sampledPoints.reduce((acc, pt, idx) => {
              const x = getX(idx)
              const y = getY(pt[cid] || 0)
              return `${acc} ${idx === 0 ? 'M' : 'L'} ${x} ${y}`
            }, '')
            const color = CAMPAIGN_COLORS[cid] || '#6366f1'
            return (
              <path
                key={cid}
                d={campPath}
                fill="none"
                stroke={color}
                strokeWidth="2"
                strokeLinecap="round"
              />
            )
          })}

          {/* Hover hit points */}
          {sampledPoints.map((pt, idx) => {
            const x = getX(idx)
            return (
              <rect
                key={idx}
                x={x - 4}
                y={padding}
                width={8}
                height={height - 2 * padding}
                fill="transparent"
                className="cursor-crosshair"
                onMouseEnter={() => setHoveredPoint({ pt, x, idx })}
                onMouseLeave={() => setHoveredPoint(null)}
              />
            )
          })}

          {/* Hover marker line */}
          {hoveredPoint && (
            <line
              x1={hoveredPoint.x}
              y1={padding}
              x2={hoveredPoint.x}
              y2={height - padding}
              stroke="#818cf8"
              strokeWidth="1.5"
              strokeDasharray="2 2"
            />
          )}
        </svg>

        {/* Floating Tooltip */}
        {hoveredPoint && (
          <div
            className="absolute top-2 pointer-events-none p-2.5 rounded-lg bg-slate-950/90 border border-slate-700 shadow-xl text-xs backdrop-blur-md z-20 font-mono"
            style={{
              left: `${Math.min(Math.max(10, (hoveredPoint.x / width) * 100), 75)}%`,
            }}
          >
            <div className="text-slate-400 font-semibold mb-1">
              {new Date(hoveredPoint.pt.t * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
            <div className="text-white font-bold mb-1">Total: {hoveredPoint.pt.total} posts/min</div>
            {campaign_ids.map((cid) => {
              const val = hoveredPoint.pt[cid] || 0
              if (val === 0) return null
              return (
                <div key={cid} style={{ color: CAMPAIGN_COLORS[cid] || '#818cf8' }}>
                  {cid.toUpperCase()}: {val} posts
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
