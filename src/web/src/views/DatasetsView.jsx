import React, { useState } from 'react'
import { Trash2, Upload } from 'lucide-react'
import { Badge, Button, Card, PageHeader, Spinner } from '../ui'
import { fmt } from '../labels'

function StatusBadge({ dataset }) {
  const job = dataset.job ?? {}
  if (job.state === 'running') return <Badge tone="accent"><Spinner className="w-3 h-3" />Analysing · step {job.step + 1}/{job.stages.length}</Badge>
  if (job.state === 'error') return <Badge tone="URGENT">Failed</Badge>
  if (dataset.analyzed) return <Badge tone="benign">Ready</Badge>
  return <Badge>Not analysed</Badge>
}

export function DatasetsView({ datasets, currentId, onOpen, onAnalyze, onDelete, onUpload }) {
  return (
    <>
      <PageHeader title="Datasets" subtitle="Bring in a batch of posts, then analyse it for coordinated campaigns." />
      <div className="grid gap-4 lg:grid-cols-12 items-start">
        <UploadCard onUpload={onUpload} className="lg:col-span-4" />

        <Card title="All datasets" className="lg:col-span-8" bodyClassName="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-subtle text-xs text-muted text-left">
              <tr>
                <th className="font-medium px-4 py-2">Name</th>
                <th className="font-medium px-4 py-2 text-right">Posts</th>
                <th className="font-medium px-4 py-2 text-right">Accounts</th>
                <th className="font-medium px-4 py-2">Status</th>
                <th className="px-4 py-2"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {datasets.map((d) => {
                const running = d.job?.state === 'running'
                return (
                  <tr key={d.id} className={d.id === currentId ? 'bg-subtle/60' : ''}>
                    <td className="px-4 py-3">
                      <div className="font-medium">{d.name}</div>
                      <div className="text-xs font-mono text-faint">{d.id}</div>
                    </td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums">{fmt(d.posts)}</td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums">{fmt(d.accounts)}</td>
                    <td className="px-4 py-3"><StatusBadge dataset={d} /></td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        <Button onClick={() => onOpen(d.id)}>Open</Button>
                        <Button variant="ghost" disabled={running} onClick={() => onAnalyze(d.id)}>
                          {d.analyzed ? 'Re-run' : 'Analyse'}
                        </Button>
                        {d.id !== 'demo' && (
                          <Button variant="ghost" className="px-2 hover:text-urgent" disabled={running}
                            onClick={() => onDelete(d)} aria-label={`Delete ${d.name}`}>
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  )
}

function UploadCard({ onUpload, className }) {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  const pick = (f) => {
    setFile(f)
    setError(null)
  }
  const submit = async () => {
    setUploading(true)
    setError(null)
    try {
      await onUpload(file)
      setFile(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <Card title="Add a dataset" className={className}>
      <label
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); if (e.dataTransfer.files[0]) pick(e.dataTransfer.files[0]) }}
        className={`flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed px-4 py-8 text-center cursor-pointer transition-colors ${dragging ? 'border-accent bg-subtle' : 'border-line hover:bg-subtle'}`}
      >
        <Upload className="w-6 h-6 text-faint" aria-hidden />
        <span className="text-sm font-medium">{file ? file.name : 'Drop a file here or choose one'}</span>
        <span className="text-xs text-muted">{file ? `${(file.size / 1e6).toFixed(1)} MB` : '.csv or .json'}</span>
        <input type="file" accept=".csv,.json" className="sr-only" onChange={(e) => e.target.files[0] && pick(e.target.files[0])} />
      </label>

      <Button variant="primary" className="w-full mt-3" disabled={!file || uploading} onClick={submit}>
        {uploading ? <><Spinner />Reading file…</> : 'Upload and analyse'}
      </Button>
      {uploading && <p className="text-xs text-muted mt-2">Large files (100 MB) take up to a minute to read.</p>}
      {error && <p className="text-sm text-urgent mt-2">{error}</p>}

      <div className="text-xs text-muted mt-4 space-y-2">
        <p className="font-medium text-ink">Each row is one post and needs</p>
        <ul className="space-y-0.5">
          <li><span className="font-mono text-ink">account</span> who posted it (account_id, user_id, author…)</li>
          <li><span className="font-mono text-ink">time</span> when (created_at, timestamp, date…; ISO or Unix time)</li>
          <li><span className="font-mono text-ink">text</span> what it says (text, content, message…)</li>
        </ul>
        <p>
          Optional, and each one improves detection: post ID, links, hashtags, reply-to, repost-of, account creation date.
          No cleaning needed. X/Twitter information-operations archives and the FiveThirtyEight IRA tweets are read as they are.
          Text-only datasets (no account or time) can't be analysed.
        </p>
        <p>
          <a href="/posts-template.csv" download className="text-accent hover:underline">Download the template CSV</a>
          <span className="text-faint"> · full guide in docs/data-format.md</span>
        </p>
      </div>
    </Card>
  )
}
