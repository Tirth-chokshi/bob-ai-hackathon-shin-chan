import React, { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'
import { ZoomIn, ZoomOut, Maximize2, RefreshCw } from 'lucide-react'

const CAMPAIGN_COLORS = {
  c1: '#8b5cf6', // Violet
  c2: '#ec4899', // Pink
  c3: '#f59e0b', // Amber
  c4: '#10b981', // Emerald
  c5: '#06b6d4', // Cyan
}

export function NetworkGraph({ graphData, selectedCampaignId, onSelectCampaign }) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !graphData || !graphData.nodes) return

    // Transform elements for Cytoscape
    const elements = [
      ...graphData.nodes.map((n) => ({
        group: 'nodes',
        data: n.data,
      })),
      ...graphData.edges.map((e) => ({
        group: 'edges',
        data: e.data,
      })),
    ]

    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      boxSelectionEnabled: false,
      autounselectify: false,
      layout: {
        name: 'cose',
        animate: false,
        randomize: false,
        componentSpacing: 100,
        nodeOverlap: 20,
        idealEdgeLength: 60,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 300,
      },
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (ele) => {
              const camp = ele.data('campaign')
              return camp ? CAMPAIGN_COLORS[camp] || '#6366f1' : '#475569'
            },
            width: (ele) => Math.min(32, Math.max(12, 10 + (ele.data('degree') || 1) * 0.8)),
            height: (ele) => Math.min(32, Math.max(12, 10 + (ele.data('degree') || 1) * 0.8)),
            label: 'data(label)',
            color: '#cbd5e1',
            'font-size': '9px',
            'font-family': 'monospace',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'text-outline-width': 1.5,
            'text-outline-color': '#020617',
          },
        },
        {
          selector: 'edge',
          style: {
            width: (ele) => Math.min(4, Math.max(1, (ele.data('weight') || 1) * 0.5)),
            'line-color': '#334155',
            'curve-style': 'bezier',
            opacity: 0.6,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#ffffff',
            'border-opacity': 0.9,
          },
        },
      ],
    })

    cy.on('tap', 'node', (evt) => {
      const camp = evt.target.data('campaign')
      if (camp && onSelectCampaign) {
        onSelectCampaign(camp)
      }
    })

    cyRef.current = cy

    return () => {
      cy.destroy()
    }
  }, [graphData])

  // Highlight selected campaign nodes
  useEffect(() => {
    if (!cyRef.current) return
    const cy = cyRef.current

    cy.batch(() => {
      cy.nodes().forEach((node) => {
        const camp = node.data('campaign')
        if (selectedCampaignId) {
          if (camp === selectedCampaignId) {
            node.style('opacity', 1)
            node.style('border-width', 2)
            node.style('border-color', '#ffffff')
          } else {
            node.style('opacity', 0.25)
            node.style('border-width', 0)
          }
        } else {
          node.style('opacity', 1)
          node.style('border-width', 0)
        }
      })

      cy.edges().forEach((edge) => {
        if (selectedCampaignId) {
          const srcCamp = edge.source().data('campaign')
          const tgtCamp = edge.target().data('campaign')
          if (srcCamp === selectedCampaignId && tgtCamp === selectedCampaignId) {
            edge.style('opacity', 0.8)
            edge.style('line-color', CAMPAIGN_COLORS[selectedCampaignId] || '#6366f1')
          } else {
            edge.style('opacity', 0.05)
            edge.style('line-color', '#334155')
          }
        } else {
          edge.style('opacity', 0.6)
          edge.style('line-color', '#334155')
        }
      })
    })
  }, [selectedCampaignId])

  const handleZoomIn = () => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 1.25)
  const handleZoomOut = () => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 0.8)
  const handleFit = () => cyRef.current && cyRef.current.fit(undefined, 30)
  const handleResetLayout = () => {
    if (!cyRef.current) return
    cyRef.current.layout({ name: 'cose', animate: true, animationDuration: 500 }).run()
  }

  return (
    <div className="relative w-full h-[620px] rounded-2xl bg-slate-950/80 border border-slate-800 overflow-hidden shadow-2xl">
      {/* Cytoscape Container */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Floating Toolbar Controls */}
      <div className="absolute top-4 right-4 flex items-center gap-1.5 p-1.5 rounded-xl bg-slate-900/90 border border-slate-700/80 backdrop-blur-md shadow-lg z-10">
        <button
          onClick={handleZoomIn}
          title="Zoom In"
          className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          title="Zoom Out"
          className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={handleFit}
          title="Fit to Center"
          className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <button
          onClick={handleResetLayout}
          title="Recompute Layout"
          className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Graph Legend Overlay */}
      <div className="absolute bottom-4 left-4 p-3 rounded-xl bg-slate-900/90 border border-slate-800 backdrop-blur-md text-xs z-10 space-y-1.5 font-mono">
        <div className="font-semibold text-slate-300 uppercase tracking-wider text-[10px] mb-1">
          Cluster Legend
        </div>
        <div className="flex items-center gap-2 text-slate-300">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CAMPAIGN_COLORS.c1 }}></span>
          Campaign C1 (Link Ring)
        </div>
        <div className="flex items-center gap-2 text-slate-300">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CAMPAIGN_COLORS.c2 }}></span>
          Campaign C2 (Rumour Ring)
        </div>
        <div className="flex items-center gap-2 text-slate-300">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CAMPAIGN_COLORS.c3 }}></span>
          Campaign C3 (Harassment Pile-on)
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-600"></span>
          Background Noise
        </div>
      </div>
    </div>
  )
}
