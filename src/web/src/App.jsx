import React, { useState, useEffect } from 'react'
import { Navbar } from './components/Navbar'
import { UploadPanel } from './components/UploadPanel'
import { StatTiles } from './components/StatTiles'
import { TimelineChart } from './components/TimelineChart'
import { CampaignList } from './components/CampaignList'
import { NetworkGraph } from './components/NetworkGraph'
import { CampaignPanel } from './components/CampaignPanel'
import { BriefView } from './components/BriefView'
import { api } from './api'
import { AlertCircle } from 'lucide-react'

export default function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const [bobConfigured, setBobConfigured] = useState(false)
  const [datasets, setDatasets] = useState([])
  const [currentDatasetId, setCurrentDatasetId] = useState('demo')

  // Analysis State
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [graphData, setGraphData] = useState(null)
  const [timelineData, setTimelineData] = useState(null)
  const [campaigns, setCampaigns] = useState([])

  // Selected Campaign & Verdicts
  const [selectedCampaignId, setSelectedCampaignId] = useState(null)
  const [selectedCampaignDetails, setSelectedCampaignDetails] = useState(null)
  const [verdicts, setVerdicts] = useState({})
  const [verdictLoading, setVerdictLoading] = useState(false)
  const [errorBanner, setErrorBanner] = useState(null)

  // 1. Initial Status & Datasets Check
  useEffect(() => {
    async function init() {
      try {
        const statusRes = await api.status()
        setBobConfigured(statusRes.bob_configured)

        const dsRes = await api.datasets()
        setDatasets(dsRes)
        if (dsRes && dsRes.length > 0) {
          const defaultId = dsRes[0].id
          setCurrentDatasetId(defaultId)
          loadDatasetArtifacts(defaultId)
        }
      } catch (err) {
        console.error('Initialization error:', err)
      }
    }
    init()
  }, [])

  // 2. Load Dataset Artifacts (Graph, Timeline, Campaigns)
  const loadDatasetArtifacts = async (dsId) => {
    try {
      const [gData, tData] = await Promise.all([
        api.graph(dsId).catch(() => null),
        api.timeline(dsId).catch(() => null),
      ])
      if (gData) setGraphData(gData)
      if (tData) {
        setTimelineData(tData)
      }

      // Check if campaigns exist in demo
      const demoDs = datasets.find((d) => d.id === dsId)
      if (demoDs && demoDs.analyzed && !analysisResult) {
        // Fetch c1 if available
        api.campaign(dsId, 'c1')
          .then((camp1) => {
            if (camp1) {
              setSelectedCampaignId('c1')
              setSelectedCampaignDetails(camp1)
            }
          })
          .catch(() => {})
      }
    } catch (err) {
      console.warn('Artifacts load error:', err)
    }
  }

  // 3. Select Campaign
  const handleSelectCampaign = async (cid) => {
    if (!cid) return
    setSelectedCampaignId(cid)
    try {
      const campDetails = await api.campaign(currentDatasetId, cid)
      setSelectedCampaignDetails(campDetails)
      // Check if verdict already cached
      if (!verdicts[cid]) {
        // Try calling classify quietly to retrieve cache if present
        api.classify(currentDatasetId, cid)
          .then((vData) => {
            setVerdicts((prev) => ({ ...prev, [cid]: vData }))
          })
          .catch(() => {})
      }
    } catch (err) {
      console.error('Failed to load campaign details:', err)
    }
  }

  // 4. Run Analysis
  const handleAnalyze = async (dsId) => {
    setAnalyzing(true)
    setErrorBanner(null)
    try {
      const res = await api.analyze(dsId)
      setAnalysisResult(res)
      setCampaigns(res.campaigns || [])

      // Reload artifacts
      const [gData, tData] = await Promise.all([
        api.graph(dsId),
        api.timeline(dsId),
      ])
      setGraphData(gData)
      setTimelineData(tData)

      // Auto-select top campaign
      if (res.campaigns && res.campaigns.length > 0) {
        const topCid = res.campaigns[0].id
        handleSelectCampaign(topCid)
      }
      setActiveTab('overview')
    } catch (err) {
      setErrorBanner(`Analysis failed: ${err.message}`)
    } finally {
      setAnalyzing(false)
    }
  }

  // 5. Upload Dataset
  const handleUpload = async (file) => {
    setErrorBanner(null)
    try {
      const res = await api.upload(file)
      // Refresh datasets
      const dsRes = await api.datasets()
      setDatasets(dsRes)
      return res
    } catch (err) {
      setErrorBanner(`Upload failed: ${err.message}`)
      throw err
    }
  }

  // 6. Ask Bob to Classify
  const handleClassify = async (cid) => {
    setVerdictLoading(true)
    setErrorBanner(null)
    try {
      const res = await api.classify(currentDatasetId, cid)
      setVerdicts((prev) => ({ ...prev, [cid]: res }))
    } catch (err) {
      setErrorBanner(`Bob classification error: ${err.message}`)
    } finally {
      setVerdictLoading(false)
    }
  }

  // Derived metrics
  const activeCampaignList = analysisResult?.campaigns || (graphData ? [
    { id: 'c1', size: 25, score: 92, top_hashtag: '#SundarpurExposed', signals: ['co_link', 'co_similar_tweet', 'co_tweet'] },
    { id: 'c2', size: 40, score: 89, top_hashtag: '#SundarpurAlert', signals: ['co_similar_tweet', 'co_tweet'] },
    { id: 'c3', size: 30, score: 88, top_hashtag: '#FakeNewsExposed', signals: ['co_reply', 'co_similar_tweet', 'co_tweet'] }
  ] : [])

  const postsTotal = analysisResult?.posts || (datasets[0]?.posts || 4538)
  const accountsTotal = analysisResult?.accounts || (datasets[0]?.accounts || 956)
  const maxScore = activeCampaignList.length > 0 ? Math.max(...activeCampaignList.map((c) => c.score)) : 92

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        bobConfigured={bobConfigured}
        selectedDataset={currentDatasetId}
      />

      {/* Optional Error Banner */}
      {errorBanner && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4 w-full">
          <div className="p-3.5 rounded-xl bg-red-950/60 border border-red-500/40 text-red-200 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{errorBanner}</span>
            </div>
            <button
              onClick={() => setErrorBanner(null)}
              className="text-red-400 hover:text-white text-xs font-semibold cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Main Tab Content */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
        {activeTab === 'upload' && (
          <UploadPanel
            datasets={datasets}
            onSelectDataset={(id) => {
              setCurrentDatasetId(id)
              loadDatasetArtifacts(id)
            }}
            onUpload={handleUpload}
            onAnalyze={handleAnalyze}
            analyzing={analyzing}
            currentDatasetId={currentDatasetId}
          />
        )}

        {activeTab === 'overview' && (
          <div className="space-y-6">
            <StatTiles
              postsCount={postsTotal}
              accountsCount={accountsTotal}
              campaignsCount={activeCampaignList.length}
              maxScore={maxScore}
            />

            <TimelineChart timelineData={timelineData} />

            <CampaignList
              campaigns={activeCampaignList}
              onSelectCampaign={(cid) => {
                handleSelectCampaign(cid)
                setActiveTab('network')
              }}
              selectedCampaignId={selectedCampaignId}
            />
          </div>
        )}

        {activeTab === 'network' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-7 xl:col-span-8">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-white text-base">Multi-Signal Coordination Graph</h3>
                  <p className="text-xs text-slate-400">
                    Accounts connected by coordinated inauthentic behaviour signals (Louvain clusters)
                  </p>
                </div>
              </div>
              <NetworkGraph
                graphData={graphData}
                selectedCampaignId={selectedCampaignId}
                onSelectCampaign={(cid) => handleSelectCampaign(cid)}
              />
            </div>

            <div className="lg:col-span-5 xl:col-span-4">
              <CampaignPanel
                campaign={selectedCampaignDetails}
                verdictData={verdicts[selectedCampaignId]}
                verdictLoading={verdictLoading}
                onClassify={handleClassify}
                onClose={() => {
                  setSelectedCampaignId(null)
                  setSelectedCampaignDetails(null)
                }}
              />
            </div>
          </div>
        )}

        {activeTab === 'brief' && (
          <BriefView
            datasetId={currentDatasetId}
            briefUrl={api.briefUrl(currentDatasetId)}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>IBM Bob AI Innovation Hackathon · Team Shin-chan</span>
          <span>Bharatiya Sakshya Adhiniyam (BSA) 2023 · Section 63 Compliant Forensics</span>
        </div>
      </footer>
    </div>
  )
}
