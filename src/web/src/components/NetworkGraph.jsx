import React, { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'
import { Maximize2, ZoomIn, ZoomOut } from 'lucide-react'
import { Button } from '../ui'
import { campaignColor } from '../labels'

// Accounts (dots) joined when they repeatedly acted together; coloured by campaign
export function NetworkGraph({ graph, campaigns, selectedId, onSelect, theme }) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)
  // the graph is built once per dataset, so read the latest click handler through a ref
  const onSelectRef = useRef(onSelect)
  onSelectRef.current = onSelect

  useEffect(() => {
    if (!containerRef.current) return
    const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()
    // amplifiers are drawn larger; seeds (who started it) get a thick ring
    const size = (n) => Math.min(34, 8 + Math.sqrt(n.data('degree') || 1) * 2.5 + (n.data('role') === 'amplifier' ? 8 : 0))
    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...graph.nodes.map((n) => ({ group: 'nodes', data: n.data })),
        ...graph.edges.map((e) => ({ group: 'edges', data: e.data })),
      ],
      layout: { name: 'cose', animate: false, randomize: false, idealEdgeLength: 60, nodeOverlap: 20, gravity: 80, numIter: 500 },
      minZoom: 0.2,
      maxZoom: 3,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (n) => (n.data('campaign') ? campaignColor(n.data('campaign')) : token('--faint')),
            width: size,
            height: size,
            'border-width': 1,
            'border-color': token('--surface'),
          },
        },
        {
          selector: 'node.labelled',
          style: {
            label: 'data(label)',
            'font-size': 9,
            color: token('--ink'),
            'text-valign': 'bottom',
            'text-margin-y': 3,
            'text-background-color': token('--surface'),
            'text-background-opacity': 0.85,
            'text-background-padding': 1,
          },
        },
        { selector: 'node[role = "seed"]', style: { 'border-width': 4, 'border-color': token('--ink') } },
        { selector: 'edge', style: { width: 1, 'line-color': token('--line'), 'curve-style': 'haystack' } },
        { selector: '.dim', style: { opacity: 0.12 } },
      ],
    })
    cy.on('tap', 'node', (e) => {
      const cid = e.target.data('campaign')
      if (cid) onSelectRef.current(cid)
    })
    cy.on('mouseover', 'node', (e) => e.target.addClass('labelled'))
    cy.on('mouseout', 'node', (e) => e.target.hasClass('member') || e.target.removeClass('labelled'))
    cyRef.current = cy
    return () => cy.destroy()
  }, [graph, theme])

  // Highlight the selected campaign and label its accounts
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.batch(() => {
      cy.elements().removeClass('dim labelled member')
      if (!selectedId) return
      const members = cy.nodes().filter((n) => n.data('campaign') === selectedId)
      members.addClass('labelled member')
      cy.elements().not(members.union(members.edgesWith(members))).addClass('dim')
    })
  }, [selectedId, graph])

  const zoom = (factor) => {
    const cy = cyRef.current
    cy.zoom({ level: cy.zoom() * factor, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } })
  }

  return (
    <div>
      <div className="relative">
        <div ref={containerRef} className="h-[560px] w-full" aria-label="Coordination network graph" />
        <div className="absolute top-3 right-3 flex gap-1">
          <Button variant="secondary" className="px-2" onClick={() => zoom(1.25)} aria-label="Zoom in"><ZoomIn className="w-4 h-4" /></Button>
          <Button variant="secondary" className="px-2" onClick={() => zoom(0.8)} aria-label="Zoom out"><ZoomOut className="w-4 h-4" /></Button>
          <Button variant="secondary" className="px-2" onClick={() => cyRef.current.fit(undefined, 30)} aria-label="Fit to screen"><Maximize2 className="w-4 h-4" /></Button>
        </div>
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 px-4 py-3 border-t border-line text-xs text-muted">
        {campaigns.map((c) => (
          <button key={c.id} onClick={() => onSelect(c.id)} className="flex items-center gap-1.5 hover:text-ink cursor-pointer">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: campaignColor(c.id) }} />
            {c.id.toUpperCase()} {c.top_hashtag}
          </button>
        ))}
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-faint" />Not in a campaign</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-faint border-2 border-ink" />Started the campaign</span>
        <span className="flex items-center gap-1.5"><span className="w-3.5 h-3.5 rounded-full bg-faint" />Larger = amplifier</span>
      </div>
    </div>
  )
}
