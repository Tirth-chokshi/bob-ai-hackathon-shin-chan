import React, { useEffect, useState } from 'react'
import { Check, Circle, FileSearch, XCircle } from 'lucide-react'
import { Button, Card, ScoreBar, Spinner, StateCard } from '../ui'
import { fmt, fmtDuration } from '../labels'

export const needsAnalysis = (dataset) => !dataset.analyzed || ['running', 'error'].includes(dataset.job?.state)

// What a dataset without results shows instead: progress, failure, or the one action to take
export function AnalysisState({ dataset, onAnalyze }) {
  const job = dataset.job ?? {}
  if (job.state === 'running') return <Progress job={job} name={dataset.name} />

  if (job.state === 'error') {
    return (
      <StateCard icon={XCircle} title="Analysis failed"
        action={<Button variant="primary" onClick={() => onAnalyze(dataset.id)}>Try again</Button>}>
        <span className="font-mono text-xs break-words">{job.error}</span>
      </StateCard>
    )
  }

  const minutes = Math.round(Math.max(20, dataset.posts / 800) / 60)
  return (
    <StateCard icon={FileSearch} title="Not analysed yet"
      action={<Button variant="primary" onClick={() => onAnalyze(dataset.id)}>Analyse {fmt(dataset.posts)} posts</Button>}>
      We look for accounts that post the same text, links or replies within seconds of each other, group them into
      campaigns and score them. {minutes >= 1 ? `This takes about ${minutes} min for this file.` : 'This takes under a minute.'}
    </StateCard>
  )
}

function Progress({ job, name }) {
  const [now, setNow] = useState(Date.now() / 1000)
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now() / 1000), 1000)
    return () => clearInterval(timer)
  }, [])
  const stages = job.stages ?? []

  return (
    <Card title={`Analysing ${name}`}
      subtitle={`Step ${job.step + 1} of ${stages.length} · ${fmtDuration(now - job.started)} elapsed`}
      className="max-w-2xl mx-auto">
      <ScoreBar value={job.step} max={stages.length} />
      <ol className="mt-4 space-y-2">
        {stages.map((stage, i) => (
          <li key={stage} className="flex items-center gap-2 text-sm">
            {i < job.step ? <Check className="w-4 h-4 text-benign" />
              : i === job.step ? <Spinner className="w-4 h-4 text-accent" />
                : <Circle className="w-4 h-4 text-faint" />}
            <span className={i === job.step ? 'font-medium' : i < job.step ? 'text-muted' : 'text-faint'}>{stage}</span>
          </li>
        ))}
      </ol>
      <p className="text-xs text-muted mt-4">
        You can open other datasets while this runs. Large files take several minutes; the similar-text step is the slowest.
      </p>
    </Card>
  )
}
