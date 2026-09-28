import React, { useState } from 'react'
import { Compass, GitFork, Share2 } from 'lucide-react'
import { Card, StateCard } from '../ui'
import { NetworkGraph } from '../components/NetworkGraph'
import { PropagationFlow } from '../components/PropagationFlow'
import { fmt } from '../labels'

// Coordination network & Dissemination narrative flow view
export function NetworkView({
  datasetId,
  data,
  selectedId,
  onSelect,
  panel,
  theme,
  onOpenPosts,
}) {
  const { graph, campaigns } = data
  const [activeTab, setActiveTab] = useState('graph') // 'graph' | 'flow'

  if (graph.nodes.length === 0) {
    return (
      <StateCard icon={Share2} title="No coordination found">
        No two accounts repeatedly posted the same text, link or reply within seconds of each
        other, so there is no network to draw.
      </StateCard>
    )
  }

  const isGraph = activeTab === 'graph'

  const switcherAction = (
    <div className="inline-flex rounded-md border border-line p-0.5 bg-subtle/60">
      <button
        onClick={() => setActiveTab('graph')}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium cursor-pointer transition-colors ${
          isGraph
            ? 'bg-surface text-ink font-semibold shadow-xs'
            : 'text-muted hover:text-ink'
        }`}
      >
        <Compass className="w-3.5 h-3.5" />
        <span>Network Graph</span>
      </button>
      <button
        onClick={() => setActiveTab('flow')}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium cursor-pointer transition-colors ${
          !isGraph
            ? 'bg-surface text-ink font-semibold shadow-xs'
            : 'text-muted hover:text-ink'
        }`}
      >
        <GitFork className="w-3.5 h-3.5 text-accent" />
        <span>Dissemination Flow</span>
      </button>
    </div>
  )

  const subtitle = isGraph
    ? `${fmt(graph.nodes.length)} accounts, ${fmt(
        graph.edges.length
      )} links. Interactive directional graph. Use the toolbar to switch layouts, prune hairball links, or isolate campaigns.`
    : 'Step-by-step narrative flow: from initial seed accounts, through synchronized botnet amplifiers, to cross-platform diffusion.'

  return (
    <div className="grid gap-4 lg:grid-cols-12 items-start">
      <Card
        title="Coordination & Dissemination"
        subtitle={subtitle}
        action={switcherAction}
        className="lg:col-span-8"
        bodyClassName="p-4"
      >
        {isGraph ? (
          <NetworkGraph
            graph={graph}
            campaigns={campaigns}
            selectedId={selectedId}
            onSelect={onSelect}
            theme={theme}
          />
        ) : (
          <PropagationFlow
            datasetId={datasetId}
            campaigns={campaigns}
            selectedId={selectedId}
            onSelect={onSelect}
            onOpenPosts={onOpenPosts}
            onSwitchToGraph={() => setActiveTab('graph')}
          />
        )}
      </Card>
      <div className="lg:col-span-4 lg:sticky lg:top-[72px] lg:max-h-[calc(100vh-88px)] lg:overflow-y-auto">
        {panel}
      </div>
    </div>
  )
}
