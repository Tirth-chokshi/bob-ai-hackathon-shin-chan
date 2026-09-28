import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, Search, X as Close } from 'lucide-react'
import { api } from '../api'
import { Spinner } from '../ui'
import { Avatar, XFocusPost, XPost, xCount } from '../components/XPost'
import { campaignColor, fmt, fmtDate, langLabel, platformLabel, zoneLabel } from '../labels'

const PAGE = 40
const TABS = [['top', 'Top'], ['latest', 'Latest'], ['oldest', 'Oldest']]
const KINDS = [['', 'All posts'], ['original', 'Original posts'], ['replies', 'Replies'], ['reposts', 'Reposts'], ['quotes', 'Quotes'], ['media', 'With media']]
const SELECTS = [
  { key: 'platform', label: 'Platform', show: (v) => platformLabel(v).label },
  { key: 'language', label: 'Language', show: langLabel },
  { key: 'city', label: 'Location', show: (v) => v },
]
const CHIPS = { q: 'Search', account: 'Account', hashtag: 'Hashtag', reply_to: 'Replies to', repost_of: 'Reposts of', quote_of: 'Quotes of' }

// The dataset's posts as an X timeline: filters on the left, the timeline in the middle, trends and the most
// active accounts on the right. Opening a post shows its thread, as on x.com.
export function PostsView({ datasetId, filter, onFilter, campaigns = [] }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [open, setOpen] = useState(null) // { id, tab } of the opened post
  const [q, setQ] = useState(filter.q ?? '')
  const request = useRef(0)
  const byId = useMemo(() => Object.fromEntries(campaigns.map((c) => [c.id, c])), [campaigns])
  const sort = filter.sort ?? 'latest'

  useEffect(() => {
    const t = setTimeout(() => q !== (filter.q ?? '') && onFilter({ ...filter, q: q || undefined }), 300)
    return () => clearTimeout(t)
  }, [q])
  useEffect(() => setQ(filter.q ?? ''), [filter.q])

  const load = async (offset) => {
    const id = ++request.current
    setLoading(true)
    setError(null)
    try {
      const r = await api.posts(datasetId, { ...filter, sort, offset, limit: PAGE })
      if (id !== request.current) return
      setResult((prev) => (offset && prev ? { ...r, posts: [...prev.posts, ...r.posts] } : r))
    } catch (e) {
      if (id === request.current) setError(e.message)
    } finally {
      if (id === request.current) setLoading(false)
    }
  }
  useEffect(() => { load(0) }, [datasetId, JSON.stringify(filter)])

  const set = (key, value) => { setOpen(null); onFilter({ ...filter, [key]: value || undefined }) }
  const openPost = (id, tab = 'replies') => { setOpen({ id, tab }); window.scrollTo({ top: 0 }) }
  const chips = Object.entries(CHIPS).filter(([k]) => filter[k])
  const facets = result?.facets ?? {}

  return (
    <div className="x-feed -mx-4 lg:-mx-6 -mt-6 grid justify-center gap-x-6 lg:grid-cols-[250px_minmax(0,600px)_320px]">
      {/* Left: search filters */}
      <aside className="hidden lg:block pt-3 space-y-3">
        <div className="sticky top-[72px] space-y-3">
          <Panel title="Search filters">
            {chips.length > 0 && (
              <div className="px-4 pb-3 flex flex-wrap gap-1.5">
                {chips.map(([k, name]) => (
                  <button key={k} onClick={() => set(k, null)} className="inline-flex items-center gap-1 h-7 pl-3 pr-2 rounded-full border border-[var(--x-line)] text-[13px] hover:bg-[var(--x-hover)] cursor-pointer">
                    {name}: <strong className="max-w-[120px] truncate">{filter[k]}</strong><Close className="w-3.5 h-3.5" aria-label="Remove" />
                  </button>
                ))}
                <button onClick={() => { setOpen(null); onFilter({ sort: filter.sort }) }} className="text-[13px] text-[var(--x-blue)] hover:underline cursor-pointer">Clear all</button>
              </div>
            )}
            <Group label="Show">
              {KINDS.map(([k, label]) => (
                <Radio key={k} checked={(filter.kind ?? '') === k} onChange={() => set('kind', k)}
                  label={label} count={facets.kind?.[k || 'all']} />
              ))}
            </Group>
            {campaigns.length > 0 && (
              <Group label="Campaign">
                <Radio checked={!filter.campaign} onChange={() => set('campaign', null)} label="Any" />
                {campaigns.map((c) => (
                  <Radio key={c.id} checked={filter.campaign === c.id} onChange={() => set('campaign', c.id)} count={facets.campaign?.[c.id] ?? 0}
                    label={<span className="flex items-center gap-1.5 min-w-0"><span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: campaignColor(c.id) }} /><span className="truncate">{c.id.toUpperCase()} {c.top_hashtag ?? ''}</span></span>} />
                ))}
              </Group>
            )}
            {SELECTS.map(({ key, label, show }) => {
              const options = Object.keys(facets[key] ?? {})
              if (filter[key] && !options.includes(filter[key])) options.unshift(filter[key])
              if (options.length < 2 && !filter[key]) return null
              return (
                <Group key={key} label={label}>
                  <select value={filter[key] ?? ''} onChange={(e) => set(key, e.target.value)} aria-label={label}
                    className="w-full h-9 rounded-md border border-[var(--x-line)] bg-[var(--x-bg)] text-[15px] px-2 cursor-pointer">
                    <option value="">Any</option>
                    {options.map((o) => <option key={o} value={o}>{show(o)}{facets[key]?.[o] != null ? ` (${fmt(facets[key][o])})` : ''}</option>)}
                  </select>
                </Group>
              )
            })}
          </Panel>
        </div>
      </aside>

      {/* Middle: the timeline, or an opened post */}
      <main className="min-h-screen bg-[var(--x-bg)] border-x border-[var(--x-line)]">
        {open ? (
          <Thread datasetId={datasetId} open={open} setOpen={setOpen} onFilter={set} campaigns={byId} />
        ) : (
          <>
            <div className="sticky top-[57px] z-10 bg-[var(--x-bg)]/85 backdrop-blur-md border-b border-[var(--x-line)]">
              <div className="px-4 pt-2.5 pb-1">
                <h2 className="text-xl font-extrabold leading-6">Posts</h2>
                <p className="text-[13px] text-[var(--x-gray)]">{result ? `${fmt(result.total)} posts · times in ${zoneLabel()}` : 'Loading…'}</p>
              </div>
              <div className="flex" role="tablist">
                {TABS.map(([k, label]) => (
                  <button key={k} role="tab" aria-selected={sort === k} onClick={() => set('sort', k === 'latest' ? null : k)}
                    className="flex-1 h-[53px] hover:bg-[var(--x-hover)] cursor-pointer grid place-items-center">
                    <span className={`relative h-full flex items-center text-[15px] ${sort === k ? 'font-bold' : 'text-[var(--x-gray)] font-medium'}`}>
                      {label}
                      {sort === k && <span className="absolute bottom-0 inset-x-0 h-1 rounded-full bg-[var(--x-blue)]" />}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {filter.account && result?.posts.length > 0 && <Profile posts={result.posts} account={filter.account} total={result.total} campaigns={byId} />}
            {error && <p className="px-4 py-3 text-[15px] text-[var(--x-pink)]">{error}</p>}
            {result?.total === 0 && (
              <div className="px-8 py-12 text-center">
                <p className="text-[31px] font-extrabold leading-9">No results</p>
                <p className="mt-2 text-[15px] text-[var(--x-gray)]">Try removing a filter or searching for something else.</p>
              </div>
            )}
            {result?.posts.map((p) => <XPost key={p.post_id} post={p} onOpen={openPost} onFilter={set} campaigns={byId} />)}
            {result && result.posts.length < result.total && (
              <button onClick={() => load(result.posts.length)} disabled={loading}
                className="w-full h-14 text-[15px] text-[var(--x-blue)] hover:bg-[var(--x-hover)] cursor-pointer">
                {loading ? <Spinner className="w-5 h-5 mx-auto" /> : `Show more (${fmt(result.total - result.posts.length)} left)`}
              </button>
            )}
            {loading && !result && <div className="py-10 flex justify-center text-[var(--x-blue)]"><Spinner className="w-6 h-6" /></div>}
          </>
        )}
      </main>

      {/* Right: search, trends, campaigns, most active accounts */}
      <aside className="hidden lg:block pt-2">
        <div className="sticky top-[65px] space-y-4">
          <label className="relative block">
            <Search className="w-[18px] h-[18px] absolute left-4 top-1/2 -translate-y-1/2 text-[var(--x-gray)]" aria-hidden />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search posts"
              className="w-full h-11 pl-12 pr-4 rounded-full bg-[var(--x-input)] border border-transparent text-[15px] placeholder:text-[var(--x-gray)] focus:bg-[var(--x-bg)] focus:border-[var(--x-blue)] focus:outline-none" />
          </label>
          {Object.keys(facets.hashtag ?? {}).length > 0 && (
            <Panel title="Trends in these posts" filled>
              {Object.entries(facets.hashtag).map(([tag, n]) => (
                <button key={tag} onClick={() => set('hashtag', tag)} className="w-full text-left px-4 py-3 hover:bg-[var(--x-hover)] cursor-pointer">
                  <div className="text-[13px] text-[var(--x-gray)]">Hashtag</div>
                  <div className="text-[15px] font-bold truncate">{tag}</div>
                  <div className="text-[13px] text-[var(--x-gray)]">{xCount(n)} posts</div>
                </button>
              ))}
            </Panel>
          )}
          {facets.accounts?.length > 0 && (
            <Panel title="Most active accounts" filled>
              {facets.accounts.map((a) => (
                <div key={a.account_id} className="flex items-center gap-3 px-4 py-3 hover:bg-[var(--x-hover)]">
                  <Avatar post={a} onClick={() => set('account', a.account_id)} />
                  <div className="min-w-0 flex-1 leading-5">
                    <div className="text-[15px] font-bold truncate">{a.display_name || a.username}</div>
                    <div className="text-[15px] text-[var(--x-gray)] truncate">@{a.username} · {fmt(a.posts)} posts</div>
                  </div>
                  <button onClick={() => set('account', a.account_id)}
                    className="h-8 px-4 rounded-full bg-[var(--x-ink)] text-[var(--x-bg)] text-[14px] font-bold hover:opacity-90 cursor-pointer">Posts</button>
                </div>
              ))}
            </Panel>
          )}
        </div>
      </aside>
    </div>
  )
}

function Panel({ title, children, filled = false }) {
  return (
    <section className={`rounded-2xl overflow-hidden ${filled ? 'bg-[var(--x-panel)]' : 'border border-[var(--x-line)] bg-[var(--x-bg)]'}`}>
      <h3 className="px-4 py-3 text-xl font-extrabold leading-6">{title}</h3>
      {children}
    </section>
  )
}

function Group({ label, children }) {
  return (
    <div className="px-4 pb-3">
      <div className="text-[15px] font-bold mb-1">{label}</div>
      {children}
    </div>
  )
}

function Radio({ checked, onChange, label, count }) {
  return (
    <label className="flex items-center justify-between gap-2 py-1.5 text-[15px] cursor-pointer">
      <span className="min-w-0 flex-1">{label}</span>
      {count != null && <span className="text-[13px] text-[var(--x-gray)]">{fmt(count)}</span>}
      <input type="radio" checked={checked} onChange={onChange} className="w-[18px] h-[18px] accent-[var(--x-blue)] cursor-pointer" />
    </label>
  )
}

// A profile header when the timeline shows one account's posts, from what the posts say about it
function Profile({ posts, account, total, campaigns }) {
  const p = posts.find((x) => x.account_id === account || x.username?.toLowerCase() === account.toLowerCase()) ?? posts[0]
  const inCampaigns = [...new Set(posts.filter((x) => x.account_id === p.account_id && x.campaign).map((x) => x.campaign))]
  return (
    <div className="border-b border-[var(--x-line)]">
      <div className="h-24 bg-[var(--x-panel)]" />
      <div className="px-4 pb-3">
        <div className="-mt-10 mb-2 w-fit rounded-full border-4 border-[var(--x-bg)]"><Avatar post={p} size={80} /></div>
        <div className="text-xl font-extrabold leading-6">{p.display_name || p.username}</div>
        <div className="text-[15px] text-[var(--x-gray)]">@{p.username}</div>
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[15px] text-[var(--x-gray)]">
          {p.city && <span>{p.city}</span>}
          {p.account_created_at && <span>Joined {fmtDate(p.account_created_at)}</span>}
        </div>
        <div className="mt-2 flex flex-wrap gap-x-5 text-[15px]">
          {p.followers != null && <span><strong>{xCount(p.followers) || 0}</strong> <span className="text-[var(--x-gray)]">Followers</span></span>}
          <span><strong>{fmt(total)}</strong> <span className="text-[var(--x-gray)]">posts in this dataset</span></span>
        </div>
        {inCampaigns.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2 text-[13px]">
            {inCampaigns.map((c) => (
              <span key={c} className="inline-flex items-center gap-1.5 font-bold text-[var(--x-gray)]">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: campaignColor(c) }} />Part of coordinated campaign {c.toUpperCase()}{campaigns[c]?.top_hashtag ? ` · ${campaigns[c].top_hashtag}` : ''}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// An opened post: the conversation above it, then its replies, reposts and quotes
function Thread({ datasetId, open, setOpen, onFilter, campaigns }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => {
    setData(null)
    setError(null)
    api.thread(datasetId, open.id).then(setData).catch((e) => setError(e.message))
  }, [datasetId, open.id])
  useEffect(() => {
    const esc = (e) => e.key === 'Escape' && setOpen(null)
    window.addEventListener('keydown', esc)
    return () => window.removeEventListener('keydown', esc)
  }, [])
  const go = (id, tab = 'replies') => { setOpen({ id, tab }); window.scrollTo({ top: 0 }) }
  const tabs = data ? [['replies', 'Replies', data.replies.length], ['reposts', 'Reposts', data.reposted_by.length], ['quotes', 'Quotes', data.quotes.length]] : []

  return (
    <>
      <div className="sticky top-[57px] z-10 h-[53px] flex items-center gap-6 px-4 bg-[var(--x-bg)]/85 backdrop-blur-md">
        <button onClick={() => setOpen(null)} aria-label="Back" className="-m-2 p-2 rounded-full hover:bg-[var(--x-hover)] cursor-pointer"><ArrowLeft className="w-5 h-5" /></button>
        <h2 className="text-xl font-extrabold">Post</h2>
      </div>
      {error && <p className="px-4 py-3 text-[15px] text-[var(--x-pink)]">{error}</p>}
      {!data && !error && <div className="py-10 flex justify-center text-[var(--x-blue)]"><Spinner className="w-6 h-6" /></div>}
      {data && (
        <>
          {data.missing_parent && (
            <p className="px-4 py-3 text-[15px] text-[var(--x-gray)] border-b border-[var(--x-line)]">This conversation starts with a post that is not in this dataset.</p>
          )}
          {data.ancestors.map((a) => <XPost key={a.post_id} post={a} onOpen={go} onFilter={onFilter} campaigns={campaigns} threadLine />)}
          <XFocusPost post={data.post} onOpen={go} onFilter={onFilter} />
          <div className="flex border-b border-[var(--x-line)]" role="tablist">
            {tabs.map(([k, label, n]) => (
              <button key={k} role="tab" aria-selected={open.tab === k} onClick={() => setOpen({ ...open, tab: k })}
                className="flex-1 h-[53px] hover:bg-[var(--x-hover)] cursor-pointer grid place-items-center">
                <span className={`relative h-full flex items-center text-[15px] ${open.tab === k ? 'font-bold' : 'text-[var(--x-gray)] font-medium'}`}>
                  {label}{n ? ` ${fmt(n)}` : ''}
                  {open.tab === k && <span className="absolute bottom-0 inset-x-0 h-1 rounded-full bg-[var(--x-blue)]" />}
                </span>
              </button>
            ))}
          </div>
          {open.tab === 'replies' && data.replies.map((r) => <XPost key={r.post_id} post={r} onOpen={go} onFilter={onFilter} campaigns={campaigns} />)}
          {open.tab === 'quotes' && data.quotes.map((r) => <XPost key={r.post_id} post={r} onOpen={go} onFilter={onFilter} campaigns={campaigns} />)}
          {open.tab === 'reposts' && data.reposted_by.map((r) => (
            <div key={r.post_id} className="flex items-center gap-3 px-4 py-3 border-b border-[var(--x-line)] hover:bg-[var(--x-hover)]">
              <Avatar post={r} onClick={() => onFilter('account', r.account_id)} />
              <div className="min-w-0 flex-1 leading-5">
                <div className="text-[15px] font-bold truncate">{r.display_name || r.username}</div>
                <div className="text-[15px] text-[var(--x-gray)] truncate">@{r.username} · reposted {new Date(r.created_at * 1000).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</div>
              </div>
              {r.campaign && <span className="flex items-center gap-1.5 text-[13px] font-bold text-[var(--x-gray)]"><span className="w-2.5 h-2.5 rounded-full" style={{ background: campaignColor(r.campaign) }} />{r.campaign.toUpperCase()}</span>}
            </div>
          ))}
          {tabs.find(([k]) => k === open.tab)?.[2] === 0 && (
            <p className="px-4 py-8 text-center text-[15px] text-[var(--x-gray)]">No {open.tab} in this dataset.</p>
          )}
        </>
      )}
    </>
  )
}
