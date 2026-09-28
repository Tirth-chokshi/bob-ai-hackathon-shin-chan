import React from 'react'
import { ArrowRight } from 'lucide-react'
import { fmtWhen, platformLabel } from '../labels'

// Places (or platforms) in the order the campaign reached them: Delhi 10:02 → Ludhiana 10:48 → …
export function SpreadPath({ path, kind, span = 0 }) {
  if (!path?.length) return <p className="text-xs text-faint">No {kind} information in this dataset.</p>
  return (
    <ol className="flex flex-wrap items-center gap-1.5">
      {path.map((step, i) => (
        <li key={step.name} className="flex items-center gap-1.5">
          {i > 0 && <ArrowRight className="w-3.5 h-3.5 text-faint" aria-hidden />}
          <span className="inline-flex flex-col rounded-md border border-line px-2 py-1 leading-tight">
            <span className="text-xs font-medium">{kind === 'platform' ? platformLabel(step.name).label : step.name}</span>
            <span className="text-[11px] font-mono text-muted">{fmtWhen(step.first_seen, span)} · {step.posts} posts</span>
          </span>
        </li>
      ))}
    </ol>
  )
}
