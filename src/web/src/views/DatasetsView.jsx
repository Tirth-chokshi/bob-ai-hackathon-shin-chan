import React, { useState } from 'react'
import { AtSign, Search, Trash2, Upload } from 'lucide-react'
import { api } from '../api'
import { Badge, Button, Card, PageHeader, Spinner } from '../ui'
import { ColumnMapping } from '../components/ColumnMapping'
import { fmt, fmtTime } from '../labels'

function StatusBadge({ dataset }) {
  const job = dataset.job ?? {}
  if (job.state === 'running') return <Badge tone="accent"><Spinner className="w-3 h-3" />Analysing · step {job.step + 1}/{job.stages.length}</Badge>
  if (job.state === 'error') return <Badge tone="URGENT">Failed</Badge>
  if (dataset.needs_mapping) return <Badge tone="ALERT">Choose columns</Badge>
  if (dataset.analyzed) return <Badge tone="benign">Ready</Badge>
  return <Badge>Not analysed</Badge>
}

export function DatasetsView({ datasets, currentId, onOpen, onAnalyze, onDelete, onUpload, onMapping, onXSearch, xConfigured }) {
  const [mapping, setMapping] = useState(null) // an upload waiting for its columns: { dataset_id, name, columns, rows, suggested }
  const [error, setError] = useState(null)
  const chooseColumns = async (d) => {
    setError(null)
    try {
      setMapping(await api.columns(d.id))
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <>
      <PageHeader title="Datasets" subtitle="Bring in posts from a file or from X, then analyse them for coordinated campaigns." />
      {error && <p className="text-sm text-urgent mb-3">{error}</p>}
      {mapping && (
        <div className="mb-4">
          <ColumnMapping upload={mapping} onCancel={() => setMapping(null)}
            onConfirm={async (id, m) => { await onMapping(id, m); setMapping(null) }} />
        </div>
      )}
      <div className="grid gap-4 lg:grid-cols-12 items-start">
        <div className="lg:col-span-4 space-y-4">
          <UploadCard onUpload={async (file) => { const res = await onUpload(file); if (res?.needs_mapping) setMapping(res) }} />
          <XSearchCard onSearch={onXSearch} configured={xConfigured} />
        </div>

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
              {datasets.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-10 text-center text-sm text-muted">
                  No datasets yet. Upload an export or search X to start.
                </td></tr>
              )}
              {datasets.map((d) => {
                const running = d.job?.state === 'running'
                return (
                  <tr key={d.id} className={d.id === currentId ? 'bg-subtle/60' : ''}>
                    <td className="px-4 py-3">
                      <div className="font-medium">{d.name}</div>
                      {d.description && <div className="text-xs text-muted mt-0.5 max-w-md">{d.description}</div>}
                      <div className="text-xs font-mono text-faint mt-0.5">
                        {d.source === 'x_api' ? `X search · fetched ${fmtTime(d.fetched_at, true)}` : d.id}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums">{fmt(d.posts)}</td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums">{fmt(d.accounts)}</td>
                    <td className="px-4 py-3"><StatusBadge dataset={d} /></td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        {d.needs_mapping ? (
                          <Button variant="primary" onClick={() => chooseColumns(d)}>Choose columns</Button>
                        ) : (
                          <>
                            <Button onClick={() => onOpen(d.id)}>Open</Button>
                            <Button variant="ghost" disabled={running} onClick={() => onAnalyze(d.id)}>
                              {d.analyzed ? 'Re-run' : 'Analyse'}
                            </Button>
                          </>
                        )}
                        {(
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

function UploadCard({ onUpload, className = '' }) {
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
        <span className="text-xs text-muted">{file ? `${(file.size / 1e6).toFixed(1)} MB` : 'CSV, Excel, JSON, X API data, WhatsApp or Telegram export'}</span>
        <input type="file" accept=".csv,.tsv,.xlsx,.json,.jsonl,.ndjson,.txt" className="sr-only" onChange={(e) => e.target.files[0] && pick(e.target.files[0])} />
      </label>

      <Button variant="primary" className="w-full mt-3" disabled={!file || uploading} onClick={submit}>
        {uploading ? <><Spinner />Reading file…</> : 'Upload and analyse'}
      </Button>
      {uploading && <p className="text-xs text-muted mt-2">Large files (100 MB) take up to a minute to read.</p>}
      {error && <p className="text-sm text-urgent mt-2">{error}</p>}

      <div className="text-xs text-muted mt-4 space-y-2">
        <p className="font-medium text-ink">Each post needs who posted it, when, and what it says</p>
        <p>
          Any column names work: they are matched by name, and if that fails you pick them from the file's first rows.
          Optional columns (platform, town, links, reply-to, repost-of, account creation date…) each add a signal.
        </p>
        <p>
          Read as they are: X API search results and stream output (JSON or JSON Lines, v2 and v1.1), WhatsApp chat
          exports (.txt), Telegram Desktop exports (result.json), X information-operations archives and the
          FiveThirtyEight IRA tweets.
        </p>
        <p>
          <a href="/posts-template.csv" download className="text-accent hover:underline">Download an example CSV</a>
          <span className="text-faint"> · full guide in docs/data-format.md</span>
        </p>
      </div>
    </Card>
  )
}

// Pulls the last 7 days of posts matching a query from X's recent-search API into a new dataset
function XSearchCard({ onSearch, configured }) {
  const [query, setQuery] = useState('')
  const [max, setMax] = useState(500)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await onSearch(query, max)
      setQuery('')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Card title="Search X" subtitle="Posts from the last 7 days, straight from the X API">
      <form onSubmit={submit} className="space-y-2">
        <label className="relative block">
          <AtSign className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-faint" aria-hidden />
          <input value={query} onChange={(e) => setQuery(e.target.value)} disabled={!configured || busy}
            placeholder='#RajpuraBachao OR "bachcha chor" -is:retweet'
            className="w-full h-9 pl-8 pr-3 rounded-md border border-line bg-surface text-sm placeholder:text-faint disabled:opacity-60" />
        </label>
        <div className="flex gap-2">
          <select value={max} onChange={(e) => setMax(Number(e.target.value))} disabled={!configured || busy}
            aria-label="How many posts" className="h-8 rounded-md border border-line bg-surface text-sm px-2 cursor-pointer">
            {[100, 500, 1000, 5000].map((n) => <option key={n} value={n}>up to {fmt(n)} posts</option>)}
          </select>
          <Button variant="primary" className="flex-1" disabled={!configured || busy || !query.trim()} type="submit">
            {busy ? <><Spinner /> Fetching…</> : <><Search className="w-4 h-4" /> Fetch and analyse</>}
          </Button>
        </div>
        {error && <p className="text-sm text-urgent">{error}</p>}
        <p className="text-xs text-muted">
          {configured
            ? 'Uses X search operators (OR, quotes, -is:retweet, lang:hi, has:links). Authors, retweets, replies, links and locations come with the posts.'
            : 'Add X_BEARER_TOKEN to src/.env (an X API plan that includes recent search) and restart the server to turn this on.'}
        </p>
      </form>
    </Card>
  )
}
