import React, { useState } from 'react'
import { AlertTriangle, Check, Minus } from 'lucide-react'
import { Button, Card, Spinner } from '../ui'

// Every field the engine reads, in the order people think about them. The first three are needed.
const FIELDS = [
  { key: 'account_id', label: 'Who posted it', hint: 'account, user ID, sender, handle', required: true },
  { key: 'created_at', label: 'When', hint: 'date and time of the post', required: true },
  { key: 'text', label: 'What it says', hint: 'the post or message text', required: true },
  { key: 'username', label: 'Display name', hint: 'shown instead of the account ID' },
  { key: 'post_id', label: 'Post ID', hint: 'lets IBM Bob and the brief cite posts' },
  { key: 'platform', label: 'Platform', hint: 'X, WhatsApp, Facebook…' },
  { key: 'city', label: 'Town or location', hint: 'draws the spread map' },
  { key: 'language', label: 'Language', hint: 'detected from the text if missing' },
  { key: 'urls', label: 'Links', hint: 'taken from the text if missing' },
  { key: 'hashtags', label: 'Hashtags', hint: 'taken from the text if missing' },
  { key: 'reply_to', label: 'Reply to (post ID)', hint: 'finds pile-ons' },
  { key: 'repost_of', label: 'Repost of (post ID)', hint: 'finds retweet rings' },
  { key: 'account_created_at', label: 'Account created', hint: 'flags brand-new accounts' },
]

// What the engine can look for with the chosen columns
function capabilities(m) {
  return [
    ['Same or similar text posted together', m.account_id && m.created_at && m.text],
    ['Same link or video shared together', m.account_id && m.created_at && m.text],
    ['Replies piling on the same post', m.reply_to],
    ['Reposting the same post', m.repost_of],
    ['Brand-new accounts', m.account_created_at],
    ['Spread across platforms and towns', m.platform || m.city],
  ]
}

// Shown after uploading a table whose columns couldn't all be matched by name: the file's first rows, a guess for
// each field (from column names and values), and what the engine will be able to find with them.
export function ColumnMapping({ upload, onConfirm, onCancel }) {
  const [mapping, setMapping] = useState(() => Object.fromEntries(FIELDS.map((f) => [f.key, upload.suggested?.[f.key] ?? ''])))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const missing = FIELDS.filter((f) => f.required && !mapping[f.key])
  const noBehaviour = !mapping.account_id || !mapping.created_at

  const confirm = async () => {
    setBusy(true)
    setError(null)
    try {
      await onConfirm(upload.dataset_id, Object.fromEntries(Object.entries(mapping).filter(([, v]) => v)))
    } catch (e) {
      setError(e.message)
      setBusy(false)
    }
  }

  return (
    <Card title="Which column is which?"
      subtitle={`${upload.name}: not every column could be matched by its name. Check the guesses; the first three are needed.`}>
      <div className="space-y-4">
        <div className="overflow-x-auto border border-line rounded-md">
          <table className="text-xs">
            <thead className="bg-subtle text-muted">
              <tr>{upload.columns.map((c) => (
                <th key={c} className="px-2 py-1.5 text-left font-medium whitespace-nowrap">
                  {c}
                  {Object.entries(mapping).filter(([, v]) => v === c).map(([k]) => (
                    <span key={k} className="ml-1 px-1 rounded bg-accent text-accent-ink font-normal">{FIELDS.find((f) => f.key === k)?.label}</span>
                  ))}
                </th>
              ))}</tr>
            </thead>
            <tbody className="divide-y divide-line">
              {upload.rows.map((r, i) => (
                <tr key={i}>{upload.columns.map((c) => <td key={c} className="px-2 py-1.5 max-w-[240px] truncate" title={r[c]}>{r[c]}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
          {FIELDS.map((f) => (
            <label key={f.key} className="flex items-center gap-2 text-sm">
              <span className="w-40 shrink-0">
                {f.label}{f.required && <span className="text-urgent"> *</span>}
                <span className="block text-[11px] text-faint leading-tight">{f.hint}</span>
              </span>
              <select value={mapping[f.key]} onChange={(e) => setMapping({ ...mapping, [f.key]: e.target.value })}
                className={`h-8 flex-1 min-w-0 rounded-md border bg-surface text-sm px-2 cursor-pointer ${f.required && !mapping[f.key] ? 'border-urgent' : 'border-line'}`}>
                <option value="">— not in this file —</option>
                {upload.columns.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </label>
          ))}
        </div>

        <div className="rounded-md bg-subtle p-3 text-xs">
          <div className="font-medium mb-1.5">With these columns the engine can find</div>
          <ul className="grid sm:grid-cols-2 gap-1">
            {capabilities(mapping).map(([label, ok]) => (
              <li key={label} className={`flex items-center gap-1.5 ${ok ? '' : 'text-faint'}`}>
                {ok ? <Check className="w-3.5 h-3.5 text-benign" aria-hidden /> : <Minus className="w-3.5 h-3.5" aria-hidden />}{label}
              </li>
            ))}
          </ul>
        </div>

        {noBehaviour && (
          <p className="flex gap-2 text-sm text-alert">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" aria-hidden />
            <span>
              Without who posted and when, accounts acting together can't be found. Files with only text and a label
              (such as fact-check or hate-speech datasets) describe content, not behaviour; add the account and time
              columns if your export has them.
            </span>
          </p>
        )}
        {error && <p className="text-sm text-urgent">{error}</p>}
        <div className="flex gap-2">
          <Button variant="primary" disabled={missing.length > 0 || busy} onClick={confirm}>
            {busy ? <><Spinner /> Reading the file…</> : 'Read the file and analyse'}
          </Button>
          <Button variant="ghost" onClick={onCancel}>Later</Button>
        </div>
      </div>
    </Card>
  )
}
