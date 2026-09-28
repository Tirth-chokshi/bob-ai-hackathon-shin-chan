import React from 'react'
import { langLabel, platformLabel } from '../labels'

// Small neutral chips: WA / X / FB / TG / IG, and हिंदी / Hinglish / English
export function PlatformChip({ platform }) {
  const p = platformLabel(platform)
  return (
    <span title={p.label} className="inline-flex items-center h-5 px-1.5 rounded border border-line bg-surface text-[11px] font-semibold text-muted">
      {p.short}
    </span>
  )
}

export function PlatformChips({ names = [] }) {
  return <span className="inline-flex flex-wrap gap-1">{names.map((n) => <PlatformChip key={n} platform={n} />)}</span>
}

// Most used first; the rest are summed as "+2" so a multilingual campaign stays one line
export function LangChips({ languages = {}, max = 3 }) {
  const codes = Object.keys(languages).sort((a, b) => languages[b] - languages[a])
  return (
    <span className="inline-flex flex-wrap gap-1">
      {codes.slice(0, max).map((l) => (
        <span key={l} className="inline-flex items-center h-5 px-1.5 rounded bg-subtle text-[11px] text-muted">{langLabel(l)}</span>
      ))}
      {codes.length > max && <span className="inline-flex items-center h-5 px-1 text-[11px] text-faint" title={codes.slice(max).map(langLabel).join(', ')}>+{codes.length - max}</span>}
    </span>
  )
}
