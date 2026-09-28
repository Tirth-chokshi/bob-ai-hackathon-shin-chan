import React, { useEffect, useRef, useState } from 'react'
import { BarChart2, Copy, ExternalLink, Heart, Image as ImageIcon, MessageCircle, MoreHorizontal, Play, Repeat2, Share, User } from 'lucide-react'
import { campaignColor, getDisplayZone, platformLabel, zoneLabel } from '../labels'

// Posts drawn the way x.com draws them, from the dataset's own data. Counts are never made up: they are the
// platform's (X API, X archives) when the source has them, otherwise the replies/reposts/quotes found in this dataset.

export const xCount = (n) => {
  if (!n) return ''
  if (n < 1000) return String(n)
  if (n < 10000) return `${(n / 1000).toFixed(1).replace(/\.0$/, '')}K`
  if (n < 1e6) return `${Math.floor(n / 1000)}K`
  return `${(n / 1e6).toFixed(1).replace(/\.0$/, '')}M`
}

// "3h", "Sep 22" or "Sep 22, 2020", as in the timeline
export const xTime = (t) => {
  const age = Date.now() / 1000 - t
  if (age >= 0 && age < 3600) return `${Math.max(1, Math.floor(age / 60))}m`
  if (age >= 0 && age < 86400) return `${Math.floor(age / 3600)}h`
  const sameYear = new Date(t * 1000).getFullYear() === new Date().getFullYear()
  return new Date(t * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric', ...(!sameYear && { year: 'numeric' }), timeZone: getDisplayZone() })
}

// "10:02 AM · Sep 22, 2020", as under an opened post
export const xFullTime = (t) => {
  const d = new Date(t * 1000)
  const opts = { timeZone: getDisplayZone() }
  return `${d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', ...opts })} · ${d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', ...opts })}`
}

const AVATAR_COLORS = ['#1d9bf0', '#7856ff', '#f91880', '#00ba7c', '#ff7a00', '#ffd400', '#794bc4', '#17bf63', '#e0245e', '#657786']
const colorFor = (s = '') => AVATAR_COLORS[[...s].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7) % AVATAR_COLORS.length]
const isPhone = (s = '') => /^\+?\d[\d\sX]{6,}$/.test(s)

// No profile photos are fetched (an investigator's browser should not call the platform), so a letter stands in
export function Avatar({ post, size = 40, onClick }) {
  const name = (post.display_name || post.username || '?').replace(/^@/, '')
  return (
    <button type="button" onClick={onClick} aria-label={`Posts by ${post.username}`}
      className="shrink-0 rounded-full grid place-items-center text-white font-bold cursor-pointer hover:opacity-90"
      style={{ width: size, height: size, background: colorFor(post.username), fontSize: size * 0.42 }}>
      {isPhone(post.username) ? <User style={{ width: size * 0.5, height: size * 0.5 }} aria-hidden /> : name.charAt(0).toUpperCase()}
    </button>
  )
}

function Verified() {
  return (
    <svg viewBox="0 0 22 22" className="w-[18px] h-[18px] shrink-0" aria-label="Verified account" role="img">
      <path fill="var(--x-blue)" d="M20.4 11c0-1.2-.7-2.3-1.7-2.8.4-1.1.2-2.4-.6-3.2-.8-.8-2.1-1.1-3.2-.6C14.3 3.3 13.2 2.6 11 2.6s-3.3.7-3.9 1.8c-1.1-.5-2.4-.2-3.2.6-.8.8-1 2.1-.6 3.2-1 .5-1.7 1.6-1.7 2.8s.7 2.3 1.7 2.8c-.4 1.1-.2 2.4.6 3.2.8.8 2.1 1.1 3.2.6.6 1.1 1.7 1.8 3.9 1.8s3.3-.7 3.9-1.8c1.1.5 2.4.2 3.2-.6.8-.8 1-2.1.6-3.2 1-.5 1.7-1.6 1.7-2.8z" />
      <path fill="#fff" d="M9.6 14.6 6.4 11.4l1.4-1.4 1.8 1.8 4.6-4.6 1.4 1.4z" />
    </svg>
  )
}

const handleOf = (p) => (p.platform === 'whatsapp' || isPhone(p.username) ? p.username : `@${(p.username || p.account_id).replace(/^@/, '')}`)
const onX = (p) => p.platform === 'x' && /^\d+$/.test(p.post_id) ? `https://x.com/${p.username}/status/${p.post_id}` : null
const stop = (fn) => (e) => { e.stopPropagation(); fn?.(e) }

// Links shortened the way X displays them; hashtags and mentions become filters
export function XText({ text, onFilter, className = '' }) {
  if (!text) return null
  const parts = text.replace(/\n{3,}/g, '\n\n').split(/(https?:\/\/\S+|#[\p{L}\p{M}\p{N}_]+|@\w+)/u)
  return (
    <div className={`whitespace-pre-wrap break-words ${className}`}>
      {parts.map((part, i) => {
        if (!part) return null
        if (/^https?:\/\//.test(part)) {
          const shown = part.replace(/^https?:\/\/(www\.)?/, '')
          return <a key={i} href={part} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}
            className="text-[var(--x-blue)] hover:underline">{shown.length > 26 ? `${shown.slice(0, 26)}…` : shown}</a>
        }
        if (part[0] === '#') return <button key={i} onClick={stop(() => onFilter('hashtag', part))} className="text-[var(--x-blue)] hover:underline cursor-pointer">{part}</button>
        if (part[0] === '@') return <button key={i} onClick={stop(() => onFilter('account', part.slice(1)))} className="text-[var(--x-blue)] hover:underline cursor-pointer">{part}</button>
        return part
      })}
    </div>
  )
}

// A repost shows the reposted post, with "<name> reposted" above. If the original isn't in the dataset, its author and
// text come from the repost itself ("RT @user: …").
export function unwrap(p) {
  if (!p.repost_of) return { shown: p, reposter: null }
  if (p.original) return { shown: p.original, reposter: p }
  const m = /^RT @(\w+):\s?/.exec(p.text || '')
  return {
    shown: { ...p, account_id: m ? m[1] : p.account_id, username: m ? m[1] : p.username, display_name: null, verified: null,
      followers: null, text: m ? p.text.slice(m[0].length) : p.text, repost_of: null, _outside: true },
    reposter: p,
  }
}

function Header({ p, onFilter, stacked = false }) {
  const via = p.platform && p.platform !== 'x' ? platformLabel(p.platform).label : null
  const name = (
    <button onClick={stop(() => onFilter('account', p.account_id))} className="flex items-center gap-0.5 min-w-0 font-bold hover:underline cursor-pointer">
      <span className="truncate">{p.display_name || p.username}</span>
      {p.verified && <Verified />}
    </button>
  )
  const handle = <span className="truncate text-[var(--x-gray)]">{handleOf(p)}</span>
  if (stacked) return <div className="min-w-0 leading-5">{name}<div className="text-[15px]">{handle}</div></div>
  return (
    <div className="flex items-center gap-1 min-w-0 text-[15px] leading-5">
      {name}
      {handle}
      <span className="text-[var(--x-gray)]">·</span>
      <time className="shrink-0 text-[var(--x-gray)] hover:underline" title={`${xFullTime(p.created_at)} (${zoneLabel()})`}>{xTime(p.created_at)}</time>
      {via && <span className="shrink-0 text-[var(--x-gray)]">· {via}</span>}
    </div>
  )
}

function Media({ types }) {
  if (!types?.length) return null
  return (
    <div className="mt-3 grid gap-0.5 rounded-2xl overflow-hidden border border-[var(--x-line)]" style={{ gridTemplateColumns: types.length > 1 ? '1fr 1fr' : '1fr' }}>
      {types.slice(0, 4).map((t, i) => (
        <div key={i} className="aspect-video bg-[var(--x-panel)] grid place-items-center text-[var(--x-gray)] text-[13px]">
          <span className="flex items-center gap-1.5">
            {t === 'photo' ? <ImageIcon className="w-4 h-4" aria-hidden /> : <Play className="w-4 h-4" aria-hidden />}
            {t === 'photo' ? 'Photo' : t === 'animated_gif' ? 'GIF' : 'Video'} · not loaded
          </span>
        </div>
      ))}
    </div>
  )
}

export function QuoteCard({ p, onOpen, onFilter }) {
  return (
    <div role="link" tabIndex={0} onClick={stop(() => onOpen(p.post_id))}
      className="mt-3 rounded-2xl border border-[var(--x-line)] px-3 py-2.5 hover:bg-[var(--x-hover)] cursor-pointer">
      <div className="flex items-center gap-1.5 min-w-0 text-[15px]">
        <Avatar post={p} size={20} onClick={stop(() => onFilter('account', p.account_id))} />
        <Header p={p} onFilter={onFilter} />
      </div>
      <XText text={p.text} onFilter={onFilter} className="mt-1 text-[15px] leading-5 line-clamp-4" />
      <Media types={p.media} />
    </div>
  )
}

function Menu({ p, onFilter }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const ref = useRef(null)
  useEffect(() => {
    if (!open) return
    const close = (e) => !ref.current?.contains(e.target) && setOpen(false)
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [open])
  const copy = () => { navigator.clipboard?.writeText(p.post_id); setCopied(true); setTimeout(() => setCopied(false), 1500) }
  const item = 'flex w-full items-center gap-3 px-4 py-3 text-[15px] font-bold text-left hover:bg-[var(--x-hover)] cursor-pointer'
  return (
    <div ref={ref} className="relative" onClick={(e) => e.stopPropagation()}>
      <button onClick={() => setOpen(!open)} aria-label="More" className="-m-2 p-2 rounded-full text-[var(--x-gray)] hover:text-[var(--x-blue)] hover:bg-[var(--x-blue)]/10 cursor-pointer">
        <MoreHorizontal className="w-[18px] h-[18px]" />
      </button>
      {open && (
        <div className="absolute right-0 top-8 z-20 w-72 rounded-xl bg-[var(--x-bg)] shadow-[0_0_15px_rgba(101,119,134,0.2),0_0_3px_1px_rgba(101,119,134,0.15)] overflow-hidden">
          <button className={item} onClick={copy}><Copy className="w-[18px] h-[18px]" />{copied ? 'Copied' : `Copy post ID (${p.post_id.slice(0, 14)}${p.post_id.length > 14 ? '…' : ''})`}</button>
          <button className={item} onClick={() => { onFilter('account', p.account_id); setOpen(false) }}><User className="w-[18px] h-[18px]" />All posts by {handleOf(p)}</button>
          {onX(p) && <a className={item} href={onX(p)} target="_blank" rel="noopener noreferrer"><ExternalLink className="w-[18px] h-[18px]" />Open on X</a>}
        </div>
      )}
    </div>
  )
}

// Reply, repost, like, views: the platform's numbers, or the ones found in this dataset (the tooltip says which)
export function Actions({ p, onOpen, big = false }) {
  const c = p.counts ?? {}
  const where = c.source === 'platform' ? 'as reported by the platform when collected' : 'found in this dataset'
  const icon = big ? 'w-[22px] h-[22px]' : 'w-[18px] h-[18px]'
  const action = (Icon, n, label, hover, onClick) => (
    <button onClick={stop(onClick)} title={n ? `${n.toLocaleString()} ${label}, ${where}` : `No ${label} ${where}`}
      className={`group flex items-center gap-1 text-[13px] text-[var(--x-gray)] cursor-pointer ${hover}`}>
      <span className="-m-2 p-2 rounded-full transition-colors group-hover:bg-current/10"><Icon className={icon} /></span>
      <span className="min-w-[1ch]">{xCount(n)}</span>
    </button>
  )
  return (
    <div className={`flex justify-between ${big ? 'px-1 py-3' : 'mt-3 mb-1.5 max-w-[425px]'}`}>
      {action(MessageCircle, c.replies, 'replies', 'hover:text-[var(--x-blue)]', () => onOpen(p.post_id, 'replies'))}
      {action(Repeat2, (c.reposts || 0) + (c.quotes || 0), 'reposts and quotes', 'hover:text-[var(--x-green)]', () => onOpen(p.post_id, 'reposts'))}
      {action(Heart, c.likes, 'likes', 'hover:text-[var(--x-pink)]', () => onOpen(p.post_id))}
      {action(BarChart2, c.views, 'views', 'hover:text-[var(--x-blue)]', () => onOpen(p.post_id))}
      <button onClick={stop(() => navigator.clipboard?.writeText(onX(p) ?? p.post_id))} title="Copy link or post ID"
        className="group text-[var(--x-gray)] hover:text-[var(--x-blue)] cursor-pointer">
        <span className="-m-2 p-2 rounded-full inline-flex group-hover:bg-current/10"><Share className={icon} /></span>
      </button>
    </div>
  )
}

// Grey lines above a post: "Rahul reposted", "Coordinated campaign C1"
function Context({ icon: Icon, children, color }) {
  return (
    <div className="flex items-center gap-3 text-[13px] font-bold text-[var(--x-gray)] leading-4 mb-1">
      <div className="w-10 flex justify-end">{Icon ? <Icon className="w-4 h-4" aria-hidden /> : <span className="w-2.5 h-2.5 mr-0.5 rounded-full" style={{ background: color }} />}</div>
      <span className="min-w-0 truncate">{children}</span>
    </div>
  )
}

// One post in a timeline. threadLine draws the line down to the next post, as X does in a conversation.
export function XPost({ post, onOpen, onFilter, threadLine = false, campaigns = {} }) {
  const { shown, reposter } = unwrap(post)
  const campaign = post.campaign && campaigns[post.campaign]
  return (
    <article onClick={() => !shown._outside && onOpen(shown.post_id)}
      className={`px-4 pt-3 ${threadLine ? '' : 'border-b border-[var(--x-line)]'} hover:bg-[var(--x-hover)] ${shown._outside ? '' : 'cursor-pointer'}`}>
      {post.campaign && (
        <Context color={campaignColor(post.campaign)}>
          <button onClick={stop(() => onFilter('campaign', post.campaign))} className="hover:underline cursor-pointer">
            Coordinated campaign {post.campaign.toUpperCase()}{campaign?.top_hashtag ? ` · ${campaign.top_hashtag}` : ''}
          </button>
        </Context>
      )}
      {reposter && (
        <Context icon={Repeat2}>
          <button onClick={stop(() => onFilter('account', reposter.account_id))} className="hover:underline cursor-pointer">
            {reposter.display_name || reposter.username} reposted
          </button>
          <span className="font-normal"> · {xTime(reposter.created_at)}</span>
        </Context>
      )}
      <div className="flex gap-3">
        <div className="flex flex-col items-center">
          <Avatar post={shown} onClick={stop(() => onFilter('account', shown.account_id))} />
          {threadLine && <div className="w-0.5 flex-1 mt-1 bg-[var(--x-thread)]" />}
        </div>
        <div className={`min-w-0 flex-1 ${threadLine ? 'pb-3' : ''}`}>
          <div className="flex items-start justify-between gap-2">
            <Header p={shown} onFilter={onFilter} />
            <Menu p={shown} onFilter={onFilter} />
          </div>
          {shown.reply_to && shown.replying_to && (
            <div className="text-[15px] text-[var(--x-gray)] leading-5">
              Replying to <button onClick={stop(() => onFilter('account', shown.replying_to))} className="text-[var(--x-blue)] hover:underline cursor-pointer">@{shown.replying_to.replace(/^@/, '')}</button>
            </div>
          )}
          <XText text={shown.text} onFilter={onFilter} className="text-[15px] leading-5 mt-0.5" />
          <Media types={shown.media} />
          {shown.quoted && <QuoteCard p={shown.quoted} onOpen={onOpen} onFilter={onFilter} />}
          {shown.quote_of && !shown.quoted && (
            <div className="mt-3 rounded-2xl border border-[var(--x-line)] px-3 py-2.5 text-[15px] text-[var(--x-gray)]">Quoted post {shown.quote_of} is not in this dataset.</div>
          )}
          <Actions p={shown._outside ? post : shown} onOpen={onOpen} />
        </div>
      </div>
    </article>
  )
}

// The opened post: large text, full time, the numbers written out, then the actions
export function XFocusPost({ post, onOpen, onFilter }) {
  const { shown, reposter } = unwrap(post)
  const c = shown.counts ?? {}
  const stats = [['reposts', 'Repost'], ['quotes', 'Quote'], ['likes', 'Like'], ['views', 'View']].filter(([k]) => c[k])
  return (
    <article className="px-4 pt-3 border-b border-[var(--x-line)]">
      {reposter && <Context icon={Repeat2}>{reposter.display_name || reposter.username} reposted</Context>}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-3 min-w-0">
          <Avatar post={shown} onClick={() => onFilter('account', shown.account_id)} />
          <Header p={shown} onFilter={onFilter} stacked />
        </div>
        <Menu p={shown} onFilter={onFilter} />
      </div>
      {shown.reply_to && shown.replying_to && (
        <div className="mt-3 text-[15px] text-[var(--x-gray)]">Replying to <button onClick={() => onFilter('account', shown.replying_to)} className="text-[var(--x-blue)] hover:underline cursor-pointer">@{shown.replying_to.replace(/^@/, '')}</button></div>
      )}
      <XText text={shown.text} onFilter={onFilter} className="mt-3 text-[17px] leading-6" />
      <Media types={shown.media} />
      {shown.quoted && <QuoteCard p={shown.quoted} onOpen={onOpen} onFilter={onFilter} />}
      <div className="my-4 text-[15px] text-[var(--x-gray)]">
        <span title={zoneLabel()}>{xFullTime(shown.created_at)}</span>
        {shown.platform && shown.platform !== 'x' && <span> · {platformLabel(shown.platform).label}</span>}
        {shown.city && <span> · {shown.city}</span>}
      </div>
      {stats.length > 0 && (
        <div className="flex flex-wrap gap-x-5 gap-y-1 py-4 border-t border-[var(--x-line)] text-[15px]">
          {stats.map(([k, label]) => (
            <span key={k}><strong className="text-[var(--x-ink)]">{c[k].toLocaleString()}</strong> <span className="text-[var(--x-gray)]">{label}{c[k] === 1 ? '' : 's'}</span></span>
          ))}
          <span className="text-[13px] text-[var(--x-gray)] self-center">{c.source === 'platform' ? 'as reported when collected' : 'found in this dataset'}</span>
        </div>
      )}
      <div className="border-t border-[var(--x-line)]"><Actions p={shown} onOpen={onOpen} big /></div>
    </article>
  )
}
