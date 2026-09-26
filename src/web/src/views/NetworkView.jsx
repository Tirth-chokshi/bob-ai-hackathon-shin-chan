import React from 'react'
import { Share2 } from 'lucide-react'
import { Card, StateCard } from '../ui'
import { NetworkGraph } from '../components/NetworkGraph'
import { fmt } from '../labels'

// Who coordinates with whom: graph on the left, the same campaign detail as Overview on the right
export function NetworkView({ data, selectedId, onSelect, panel }) {
  const { graph, campaigns } = data
  if (graph.nodes.length === 0) {
    return (
      <StateCard icon={Share2} title="No coordination found">
        No two accounts repeatedly posted the same text, link or reply within seconds of each other, so there is no network to draw.
      </StateCard>
    )
  }
  return (
    <div className="grid gap-4 lg:grid-cols-12 items-start">
      <Card title="Coordination network" className="lg:col-span-8" bodyClassName=""
        subtitle={`${fmt(graph.nodes.length)} accounts, ${fmt(graph.edges.length)} links. A line means two accounts repeatedly acted together within seconds. Click a dot to open its campaign.`}>
        <NetworkGraph graph={graph} campaigns={campaigns} selectedId={selectedId} onSelect={onSelect} />
      </Card>
      <div className="lg:col-span-4 lg:sticky lg:top-[72px] lg:max-h-[calc(100vh-88px)] lg:overflow-y-auto">
        {panel}
      </div>
    </div>
  )
}
