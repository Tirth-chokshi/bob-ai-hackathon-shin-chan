import React from 'react'
import { AlertTriangle, ShieldCheck, Sparkles } from 'lucide-react'
import { fmt, fmtRange, langLabel, platformLabel, THREATS } from '../labels'

// What each coordination signal looks like in plain words
const DOING = {
  co_tweet: 'posting the same text',
  co_similar_tweet: 'posting near-identical text',
  co_link: 'sharing the same links',
  co_reply: 'replying to the same posts',
  co_retweet: 'retweeting the same posts',
}

const list = (items) => items.length < 2 ? items.join('') : `${items.slice(0, -1).join(', ')} and ${items.at(-1)}`
const plural = (n, word) => `${fmt(n)} ${word}${n === 1 ? '' : 's'}`

// One paragraph at the top of the Overview, written from the data: what this dataset is, what was found, and
// what to do next. Replaces a row of bare numbers.
export function Summary({ stats, campaigns }) {
  const assessed = campaigns.filter((c) => c.assessment)
  const byLevel = (l) => assessed.filter((c) => c.assessment.level === l)
  const urgent = byLevel('URGENT')
  const alert = byLevel('ALERT')
  const gatherings = campaigns.filter((c) => c.assessment?.offline_event?.at)
  const unassessed = campaigns.length - assessed.length

  // The dataset: size, period, platforms, languages
  const platforms = Object.keys(stats?.platforms ?? {}).map((p) => platformLabel(p).label)
  const langs = Object.entries(stats?.languages ?? {})
  const langTotal = langs.reduce((s, [, n]) => s + n, 0)
  const langText = !langs.length ? null
    : langs[0][1] / langTotal >= 0.8 ? `mostly ${langLabel(langs[0][0])}`
    : list(langs.slice(0, 3).map(([l]) => langLabel(l)))
  const scope = stats && [
    stats.first && fmtRange(stats.first, stats.last),
    platforms.length === 1 ? `all on ${platforms[0]}` : platforms.length > 1 ? list(platforms) : null,
    langText,
  ].filter(Boolean).join(' · ')

  // What was found
  let tone = 'benign'
  let finding
  if (!campaigns.length) {
    finding = <>No coordinated campaigns: no group of 5 or more accounts repeatedly posted the same text, link or reply within seconds of each other.</>
  } else if (urgent.length || alert.length) {
    tone = urgent.length ? 'urgent' : 'alert'
    const parts = [
      urgent.length && <strong key="u" className="text-urgent">{urgent.length} urgent</strong>,
      alert.length && <strong key="a" className="text-alert">{alert.length} on alert</strong>,
    ].filter(Boolean)
    const g = gatherings[0]?.assessment.offline_event
    finding = (
      <>
        {parts.reduce((acc, p, i) => (i ? [...acc, ' and ', p] : [p]), [])}.{' '}
        {g ? <>{gatherings.length > 1 ? `${gatherings.length} planned gatherings, the first` : 'A crowd is being called'} to <strong>{g.where}</strong> (see below). </> : null}
        {list([...urgent, ...alert].map((c) => `${c.id.toUpperCase()} is ${(THREATS[c.assessment.threat_type] ?? c.assessment.threat_type).toLowerCase()}`))}.
      </>
    )
  } else {
    const top = campaigns[0]
    const doing = (top.signals ?? []).map((s) => DOING[s]).filter(Boolean)
    finding = (
      <>
        {assessed.length ? <>No threats: IBM Bob assessed {assessed.length === campaigns.length ? ({ 1: 'it', 2: 'both' }[campaigns.length] ?? `all ${campaigns.length}`) : assessed.length} as {list([...new Set(assessed.map((c) => (THREATS[c.assessment.threat_type] ?? c.assessment.threat_type).toLowerCase()))])}. </> : null}
        The largest, <strong>{top.id.toUpperCase()}</strong> ({plural(top.size, 'account')}{top.top_hashtag ? `, ${top.top_hashtag}` : ''}), keeps {list(doing.length ? doing : ['acting together'])} within seconds of each other.
      </>
    )
  }
  const Icon = tone === 'benign' ? ShieldCheck : AlertTriangle
  const iconColor = { benign: 'text-benign', urgent: 'text-urgent', alert: 'text-alert' }[tone]

  return (
    <section aria-label="Summary" className="bg-surface border border-line rounded-lg px-4 py-3.5 flex gap-3">
      <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${iconColor}`} aria-hidden />
      <div className="space-y-1 min-w-0">
        <p className="text-[15px] leading-relaxed">
          <strong>{plural(campaigns.length, 'coordinated campaign')}</strong>
          {stats && <> in {fmt(stats.posts)} posts from {fmt(stats.accounts)} accounts</>}. {finding}
        </p>
        {scope && <p className="text-xs text-muted">{scope}</p>}
        {unassessed > 0 && (
          <p className="text-xs text-muted flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-accent" aria-hidden />
            {plural(unassessed, 'campaign')} not assessed by IBM Bob yet: select one and press <strong className="text-ink">Ask IBM Bob</strong>.
          </p>
        )}
      </div>
    </section>
  )
}
