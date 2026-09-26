import React, { useCallback, useEffect, useRef, useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import { api } from './api'
import { Banner, Button, PageHeader, Spinner } from './ui'
import { fmt } from './labels'
import { AnalysisState, needsAnalysis } from './components/AnalysisState'
import { CampaignPanel } from './components/CampaignPanel'
import { DatasetsView } from './views/DatasetsView'
import { OverviewView } from './views/OverviewView'
import { NetworkView } from './views/NetworkView'
import { BriefView } from './views/BriefView'

const VIEWS = [
  { id: 'datasets', label: 'Datasets' },
  { id: 'overview', label: 'Overview' },
  { id: 'network', label: 'Network' },
  { id: 'brief', label: 'Brief' },
]
const EMPTY = { campaigns: null, graph: null, timeline: null }

// Location is kept in the URL (#/view/dataset/campaign) so a reload or a shared link opens the same place
function readHash() {
  const [view, datasetId, campaignId] = window.location.hash.replace(/^#\/?/, '').split('/')
  return { view: VIEWS.some((v) => v.id === view) ? view : 'overview', datasetId: datasetId || null, campaignId: campaignId || null }
}

export default function App() {
  const [view, setView] = useState(() => readHash().view)
  const [datasetId, setDatasetId] = useState(() => readHash().datasetId)
  const [datasets, setDatasets] = useState(null) // null while loading
  const [bobConfigured, setBobConfigured] = useState(false)
  const [data, setData] = useState(EMPTY)
  const [selectedId, setSelectedId] = useState(null)
  const [error, setError] = useState(null)
  const wantedCampaign = useRef(readHash().campaignId) // from the URL, applied once results load

  // state → URL (adds a history entry, so Back works) and URL → state (Back/Forward, edited links)
  useEffect(() => {
    const hash = `#/${view}/${datasetId ?? ''}${selectedId && view !== 'datasets' ? `/${selectedId}` : ''}`
    if (window.location.hash !== hash) window.location.hash = hash
  }, [view, datasetId, selectedId])
  useEffect(() => {
    const onHashChange = () => {
      const h = readHash()
      setView(h.view)
      if (h.datasetId) setDatasetId(h.datasetId)
      if (h.campaignId) setSelectedId(h.campaignId)
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const refreshDatasets = useCallback(async () => {
    try {
      const ds = await api.datasets()
      setDatasets(ds)
      return ds
    } catch (e) {
      setError(`Can't reach the analysis server (${e.message}). Is "python src/main.py" running?`)
      return null
    }
  }, [])

  useEffect(() => {
    api.status().then((s) => setBobConfigured(s.bob_configured)).catch(() => {})
    refreshDatasets().then((ds) => {
      if (ds && !ds.some((d) => d.id === datasetId)) setDatasetId(ds[0]?.id ?? null)
    })
  }, [])

  const dataset = datasets?.find((d) => d.id === datasetId)
  const anyRunning = datasets?.some((d) => d.job?.state === 'running')

  // Poll while any analysis runs, so progress and the finished state show up by themselves
  useEffect(() => {
    if (!anyRunning) return
    const timer = setInterval(refreshDatasets, 1500)
    return () => clearInterval(timer)
  }, [anyRunning, refreshDatasets])

  // Load results when the dataset changes or an analysis of it finishes
  const resultsKey = dataset && !needsAnalysis(dataset) ? `${dataset.id}:${dataset.job?.finished ?? ''}` : null
  useEffect(() => {
    setData(EMPTY)
    setSelectedId(null)
    if (!resultsKey) return
    let cancelled = false
    Promise.all([api.campaigns(dataset.id), api.graph(dataset.id), api.timeline(dataset.id)])
      .then(([campaigns, graph, timeline]) => {
        if (cancelled) return
        setData({ campaigns, graph, timeline })
        const wanted = campaigns.find((c) => c.id === wantedCampaign.current)
        wantedCampaign.current = null
        setSelectedId(wanted?.id ?? campaigns[0]?.id ?? null)
      })
      .catch((e) => !cancelled && setError(`Couldn't load the results for ${dataset.name}: ${e.message}`))
    return () => { cancelled = true }
  }, [resultsKey])

  const openDataset = (id, nextView = 'overview') => {
    setDatasetId(id)
    setView(nextView)
  }

  const analyse = async (id) => {
    setError(null)
    try {
      await api.analyze(id)
      await refreshDatasets()
    } catch (e) {
      setError(`Could not start the analysis: ${e.message}`)
    }
  }

  const upload = async (file) => {
    const res = await api.upload(file) // errors are shown in the upload card
    await api.analyze(res.dataset_id)
    await refreshDatasets()
    openDataset(res.dataset_id)
  }

  const remove = async (d) => {
    if (!window.confirm(`Delete "${d.name}" and its analysis results? This cannot be undone.`)) return
    try {
      await api.remove(d.id)
      const ds = await refreshDatasets()
      if (d.id === datasetId) setDatasetId(ds?.[0]?.id ?? null)
    } catch (e) {
      setError(`Could not delete ${d.name}: ${e.message}`)
    }
  }

  // An IBM Bob assessment changes the campaign list badges and the brief
  const onAssessed = (cid, assessment) =>
    setData((prev) => ({ ...prev, campaigns: prev.campaigns.map((c) => (c.id === cid ? { ...c, assessment } : c)) }))

  const assessedCount = data.campaigns?.filter((c) => c.assessment).length ?? 0
  const panel = dataset && (
    <CampaignPanel datasetId={dataset.id} campaignId={selectedId} bobConfigured={bobConfigured} onAssessed={onAssessed} />
  )

  const renderDatasetPage = () => {
    if (!dataset) return null
    const title = { overview: dataset.name, network: 'Network', brief: 'Threat brief' }[view]
    const subtitle = `${fmt(dataset.posts)} posts · ${fmt(dataset.accounts)} accounts${data.campaigns ? ` · ${data.campaigns.length} campaigns` : ''}`
    const rerun = dataset.analyzed && !needsAnalysis(dataset) && view === 'overview' &&
      <Button onClick={() => analyse(dataset.id)}>Re-run analysis</Button>

    let body
    if (needsAnalysis(dataset)) body = <AnalysisState dataset={dataset} onAnalyze={analyse} />
    else if (!data.campaigns) body = <div className="flex items-center justify-center gap-2 py-24 text-sm text-muted"><Spinner />Loading results…</div>
    else if (view === 'overview') body = <OverviewView data={data} selectedId={selectedId} onSelect={setSelectedId} panel={panel} />
    else if (view === 'network') body = <NetworkView data={data} selectedId={selectedId} onSelect={setSelectedId} panel={panel} />
    else body = <BriefView key={`${dataset.id}-${assessedCount}`} url={`${api.briefUrl(dataset.id)}?v=${assessedCount}`} />

    return <><PageHeader title={title} subtitle={subtitle} action={rerun} />{body}</>
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-20 bg-surface border-b border-line">
        <div className="max-w-[1440px] mx-auto px-4 lg:px-6 min-h-14 py-2 flex flex-wrap items-center gap-x-6 gap-y-2">
          <div className="flex items-center gap-2 font-semibold">
            <ShieldCheck className="w-5 h-5 text-accent" aria-hidden />
            Threat Intel Engine
          </div>
          <nav className="flex items-center gap-1" aria-label="Pages">
            {VIEWS.map((v) => (
              <button key={v.id} onClick={() => setView(v.id)} aria-current={view === v.id ? 'page' : undefined}
                className={`h-8 px-3 rounded-md text-sm cursor-pointer transition-colors ${view === v.id ? 'bg-subtle text-ink font-medium' : 'text-muted hover:text-ink'}`}>
                {v.label}
              </button>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            {datasets && datasets.length > 0 && (
              <label className="flex items-center gap-2 text-xs text-muted">
                Dataset
                <select value={datasetId ?? ''} onChange={(e) => setDatasetId(e.target.value)}
                  className="h-8 max-w-[260px] rounded-md border border-line bg-surface text-ink text-sm px-2 cursor-pointer">
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}{d.job?.state === 'running' ? ' — analysing…' : d.analyzed ? '' : ' — not analysed'}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <span className="flex items-center gap-1.5 text-xs text-muted"
              title={bobConfigured ? 'BOB_API_KEY is set: new assessments are possible' : 'No BOB_API_KEY in src/.env: saved assessments only'}>
              <span className={`w-2 h-2 rounded-full ${bobConfigured ? 'bg-benign' : 'bg-faint'}`} />
              {bobConfigured ? 'IBM Bob ready' : 'IBM Bob: saved results only'}
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 lg:px-6 py-6">
        {error && <div className="mb-4"><Banner onClose={() => setError(null)}>{error}</Banner></div>}
        {datasets === null && !error && (
          <div className="flex items-center justify-center gap-2 py-24 text-sm text-muted"><Spinner />Connecting…</div>
        )}
        {datasets && view === 'datasets' && (
          <DatasetsView datasets={datasets} currentId={datasetId} onOpen={(id) => openDataset(id)}
            onAnalyze={(id) => { analyse(id); openDataset(id) }} onDelete={remove} onUpload={upload} />
        )}
        {datasets && view !== 'datasets' && renderDatasetPage()}
      </main>

      <footer className="border-t border-line py-3 text-center text-xs text-faint">
        Decision support only. Legal sections are suggestions to be verified by a legal officer.
      </footer>
    </div>
  )
}
