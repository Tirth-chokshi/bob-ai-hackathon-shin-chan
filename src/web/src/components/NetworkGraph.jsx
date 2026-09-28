import React, { useEffect, useMemo, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import {
  Clock,
  Compass,
  Filter,
  GitFork,
  Layers,
  Maximize2,
  Radio,
  SlidersHorizontal,
  Sparkles,
  ZoomIn,
  ZoomOut,
} from 'lucide-react'
import { Button } from '../ui'
import { campaignColor, fmtClock, fmtWhen } from '../labels'

// Prune full clique mesh into an elegant directed backbone flow
function computeBackboneEdges(nodes, edges, densityMode, minWeight) {
  // 1. Filter by min weight first
  const filtered = minWeight > 2 ? edges.filter((e) => (e.data.weight || 1) >= minWeight) : edges

  if (densityMode === 'all') {
    return filtered
  }

  // 2. Build adjacency for quick lookups
  const nodeMap = new Map(nodes.map((n) => [n.data.id, n.data]))
  const adj = new Map()
  filtered.forEach((e) => {
    const u = e.data.source
    const v = e.data.target
    if (!adj.has(u)) adj.set(u, [])
    if (!adj.has(v)) adj.set(v, [])
    adj.get(u).push(e)
    adj.get(v).push(e)
  })

  const keptEdgeIds = new Set()

  // 3. For each node, retain its top 2 highest-weight connections
  nodes.forEach((n) => {
    const list = adj.get(n.data.id) || []
    if (list.length === 0) return

    // Prioritize connections to seeds/amplifiers or highest weight
    const sorted = [...list].sort((a, b) => {
      const otherA = a.data.source === n.data.id ? a.data.target : a.data.source
      const otherB = b.data.source === n.data.id ? b.data.target : b.data.source
      const nodeA = nodeMap.get(otherA)
      const nodeB = nodeMap.get(otherB)

      const scoreA =
        (nodeA?.role === 'seed' ? 50 : nodeA?.role === 'amplifier' ? 25 : 0) + (a.data.weight || 1)
      const scoreB =
        (nodeB?.role === 'seed' ? 50 : nodeB?.role === 'amplifier' ? 25 : 0) + (b.data.weight || 1)
      return scoreB - scoreA
    })

    // Take top 2
    sorted.slice(0, 2).forEach((e) => keptEdgeIds.add(e.data.id))
  })

  // 4. Ensure seed accounts connect to amplifiers
  const seedIds = new Set(nodes.filter((n) => n.data.role === 'seed').map((n) => n.data.id))
  const ampIds = new Set(nodes.filter((n) => n.data.role === 'amplifier').map((n) => n.data.id))

  filtered.forEach((e) => {
    if (
      (seedIds.has(e.data.source) && ampIds.has(e.data.target)) ||
      (seedIds.has(e.data.target) && ampIds.has(e.data.source))
    ) {
      keptEdgeIds.add(e.data.id)
    }
  })

  return filtered.filter((e) => keptEdgeIds.has(e.data.id))
}

// Ensure edge direction points forward: Seed -> Amplifier -> Member, or Earlier -> Later
function orientEdges(nodes, edges) {
  const nodeMap = new Map(nodes.map((n) => [n.data.id, n.data]))
  const roleRank = { seed: 3, amplifier: 2, member: 1 }

  return edges.map((e) => {
    const u = nodeMap.get(e.data.source)
    const v = nodeMap.get(e.data.target)
    if (!u || !v) return e

    // 1. By role priority
    const rankU = roleRank[u.role] || 0
    const rankV = roleRank[v.role] || 0

    if (rankU > rankV) {
      return { group: 'edges', data: { ...e.data, source: u.id, target: v.id } }
    }
    if (rankV > rankU) {
      return { group: 'edges', data: { ...e.data, source: v.id, target: u.id } }
    }

    // 2. By timestamp (first seen)
    if (u.first_seen && v.first_seen && u.first_seen !== v.first_seen) {
      if (u.first_seen < v.first_seen) {
        return { group: 'edges', data: { ...e.data, source: u.id, target: v.id } }
      } else {
        return { group: 'edges', data: { ...e.data, source: v.id, target: u.id } }
      }
    }

    return { group: 'edges', data: e.data }
  })
}

// Compute timeline positions for temporal cascade layout
function computeTimelinePositions(nodes, width = 800, height = 500) {
  const times = nodes.map((n) => n.data.first_seen).filter(Boolean)
  const minT = times.length ? Math.min(...times) : 0
  const maxT = times.length ? Math.max(...times) : 1
  const span = maxT - minT || 1

  const campList = [...new Set(nodes.map((n) => n.data.campaign).filter(Boolean))]
  const positions = {}

  nodes.forEach((n) => {
    const t = n.data.first_seen || minT
    const normX = (t - minT) / span
    const x = 70 + normX * (width - 140)

    const campIdx = campList.indexOf(n.data.campaign)
    const rowHeight = campList.length > 1 ? (height - 120) / campList.length : height / 2
    const baseY = campIdx >= 0 ? 70 + campIdx * rowHeight + rowHeight / 2 : height / 2

    const roleOffset = n.data.role === 'seed' ? -35 : n.data.role === 'amplifier' ? 0 : 35
    const hash = n.data.id.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)
    const jitterY = ((hash % 9) - 4) * 6

    positions[n.data.id] = { x, y: baseY + roleOffset + jitterY }
  })
  return positions
}

export function NetworkGraph({ graph, campaigns, selectedId, onSelect, theme }) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)
  const onSelectRef = useRef(onSelect)
  onSelectRef.current = onSelect

  // State controls for de-cluttering
  const [layoutMode, setLayoutMode] = useState('cose') // 'hierarchy' | 'radial' | 'cose' | 'timeline'
  const [densityMode, setDensityMode] = useState('backbone') // 'backbone' | 'all'
  const [minWeight, setMinWeight] = useState(2) // 2 | 5 | 8
  const [isolatedCampaign, setIsolatedCampaign] = useState('all') // 'all' | cid
  const [hoveredNode, setHoveredNode] = useState(null) // for floating tooltip

  // Sync isolated campaign with selectedId if requested
  useEffect(() => {
    if (selectedId && isolatedCampaign !== 'all' && isolatedCampaign !== selectedId) {
      setIsolatedCampaign(selectedId)
    }
  }, [selectedId])

  // Filter nodes & edges according to isolation and density
  const { visibleNodes, visibleEdges, rawCount, backboneCount } = useMemo(() => {
    let nodes = graph.nodes
    if (isolatedCampaign !== 'all') {
      nodes = nodes.filter((n) => n.data.campaign === isolatedCampaign)
    }
    const nodeIds = new Set(nodes.map((n) => n.data.id))
    let edges = graph.edges.filter((e) => nodeIds.has(e.data.source) && nodeIds.has(e.data.target))

    const rawCount = edges.length
    const backboneEdges = computeBackboneEdges(nodes, edges, 'backbone', minWeight)
    const backboneCount = backboneEdges.length

    const activeEdges = computeBackboneEdges(nodes, edges, densityMode, minWeight)
    const oriented = orientEdges(nodes, activeEdges)

    return {
      visibleNodes: nodes,
      visibleEdges: oriented,
      rawCount,
      backboneCount,
    }
  }, [graph, isolatedCampaign, densityMode, minWeight])

  // Initialize and update Cytoscape
  useEffect(() => {
    if (!containerRef.current) return
    const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

    // Sizing: Amplifiers largest; seeds get thick ring
    const size = (n) =>
      Math.min(34, 9 + Math.sqrt(n.data('degree') || 1) * 2.6 + (n.data('role') === 'amplifier' ? 8 : 0))

    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...visibleNodes.map((n) => ({ group: 'nodes', data: n.data })),
        ...visibleEdges,
      ],
      minZoom: 0.15,
      maxZoom: 3.5,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (n) =>
              n.data('campaign') ? campaignColor(n.data('campaign')) : token('--faint'),
            width: size,
            height: size,
            'border-width': 1.5,
            'border-color': token('--surface'),
            'transition-property': 'background-color, border-width, opacity',
            'transition-duration': '0.15s',
          },
        },
        {
          selector: 'node.labelled',
          style: {
            label: 'data(label)',
            'font-size': 10,
            'font-weight': 600,
            color: token('--ink'),
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'text-background-color': token('--surface'),
            'text-background-opacity': 0.9,
            'text-background-padding': 2,
            'text-background-shape': 'roundrectangle',
          },
        },
        {
          selector: 'node[role = "seed"]',
          style: {
            'border-width': 4,
            'border-color': token('--ink'),
          },
        },
        {
          selector: 'node[role = "amplifier"]',
          style: {
            'border-width': 2.5,
            'border-color': token('--alert'),
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.5,
            'line-color': token('--line'),
            'target-arrow-color': token('--faint'),
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 1.2,
            'line-opacity': 0.85,
            'transition-property': 'line-color, target-arrow-color, width, opacity',
            'transition-duration': '0.15s',
          },
        },
        {
          selector: 'edge.highlighted',
          style: {
            width: 2.5,
            'line-color': token('--accent'),
            'target-arrow-color': token('--accent'),
            'arrow-scale': 1.4,
            'z-index': 99,
          },
        },
        {
          selector: '.dim',
          style: {
            opacity: 0.08,
          },
        },
      ],
    })

    // Execute active layout
    applyLayout(cy, layoutMode, visibleNodes, containerRef.current)

    // Events
    cy.on('tap', 'node', (e) => {
      const cid = e.target.data('campaign')
      if (cid) onSelectRef.current(cid)
    })

    cy.on('mouseover', 'node', (e) => {
      const node = e.target
      node.addClass('labelled')

      // Highlight 1-hop flow neighbors
      const connectedEdges = node.connectedEdges()
      const neighbors = connectedEdges.connectedNodes()

      cy.elements().not(node.union(neighbors).union(connectedEdges)).addClass('dim')
      connectedEdges.addClass('highlighted')

      const pos = e.renderedPosition || { x: e.position.x, y: e.position.y }
      setHoveredNode({
        id: node.data('id'),
        label: node.data('label'),
        campaign: node.data('campaign'),
        role: node.data('role'),
        degree: node.data('degree'),
        first_seen: node.data('first_seen'),
        visibleLinks: connectedEdges.length,
        x: pos.x,
        y: pos.y,
      })
    })

    cy.on('mouseout', 'node', (e) => {
      e.target.hasClass('member') || e.target.removeClass('labelled')
      cy.elements().removeClass('dim highlighted')
      setHoveredNode(null)
    })

    cyRef.current = cy
    return () => cy.destroy()
  }, [visibleNodes, visibleEdges, theme])

  // Apply layout helper
  const applyLayout = (cy, mode, nodes, container) => {
    if (!cy) return
    const width = container?.clientWidth || 800
    const height = container?.clientHeight || 560

    if (mode === 'hierarchy') {
      // Directed flow DAG: Seeds at top -> Amplifiers -> Members
      const roots = cy.nodes('[role = "seed"]')
      cy.layout({
        name: 'breadthfirst',
        directed: true,
        roots: roots.length > 0 ? roots : cy.nodes().slice(0, 3),
        spacingFactor: 1.25,
        avoidOverlap: true,
        animate: false,
      }).run()
    } else if (mode === 'radial') {
      // Concentric radar: Seeds in bullseye, Amplifiers in inner ring, Members in outer orbit
      cy.layout({
        name: 'concentric',
        concentric: (node) => {
          const role = node.data('role')
          if (role === 'seed') return 12
          if (role === 'amplifier') return 8
          if (node.data('campaign')) return 4
          return 1
        },
        levelWidth: () => 2.5,
        spacingFactor: 1.2,
        avoidOverlap: true,
        animate: false,
      }).run()
    } else if (mode === 'timeline') {
      // Horizontal temporal cascade from first to latest post
      const posMap = computeTimelinePositions(nodes, width, height)
      cy.layout({
        name: 'preset',
        positions: (node) => posMap[node.id()] || { x: width / 2, y: height / 2 },
        animate: false,
      }).run()
    } else {
      // Organic spread: tuned COSE with low gravity to eliminate clump hairballs
      cy.layout({
        name: 'cose',
        animate: false,
        randomize: false,
        idealEdgeLength: 110,
        nodeOverlap: 35,
        gravity: 0.15, // Low gravity lets graph breathe across canvas!
        numIter: 800,
        nodeRepulsion: () => 10000,
        edgeElasticity: () => 32,
      }).run()
    }

    cy.fit(undefined, 35)
  }

  // Switch layout mode dynamically
  const switchLayout = (mode) => {
    setLayoutMode(mode)
    if (cyRef.current) {
      applyLayout(cyRef.current, mode, visibleNodes, containerRef.current)
    }
  }

  // Campaign highlight when selectedId changes (in 'all' mode)
  useEffect(() => {
    const cy = cyRef.current
    if (!cy || isolatedCampaign !== 'all') return
    cy.batch(() => {
      cy.elements().removeClass('dim labelled member')
      if (!selectedId) return
      const members = cy.nodes().filter((n) => n.data('campaign') === selectedId)
      members.addClass('labelled member')
      cy.elements().not(members.union(members.edgesWith(members))).addClass('dim')
    })
  }, [selectedId, isolatedCampaign, visibleNodes])

  const zoom = (factor) => {
    const cy = cyRef.current
    if (!cy) return
    cy.zoom({ level: cy.zoom() * factor, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } })
  }

  return (
    <div className="space-y-2">
      {/* Top Toolbar: Layout Selector & Density Filters */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 bg-subtle/50 border border-line rounded-lg text-xs">
        {/* Layout Modes */}
        <div className="flex items-center gap-1">
          <span className="text-muted font-medium mr-1 flex items-center gap-1">
            <Compass className="w-3.5 h-3.5" /> Layout:
          </span>
          <div className="inline-flex rounded-md border border-line p-0.5 bg-surface">
            <button
              onClick={() => switchLayout('hierarchy')}
              className={`px-2 py-1 rounded text-xs font-medium cursor-pointer flex items-center gap-1 transition-colors ${
                layoutMode === 'hierarchy'
                  ? 'bg-subtle text-ink font-semibold shadow-2xs'
                  : 'text-muted hover:text-ink'
              }`}
              title="Hierarchical flow from Seeds at top to Amplifiers and Members"
            >
              <GitFork className="w-3 h-3" /> Flow
            </button>
            <button
              onClick={() => switchLayout('radial')}
              className={`px-2 py-1 rounded text-xs font-medium cursor-pointer flex items-center gap-1 transition-colors ${
                layoutMode === 'radial'
                  ? 'bg-subtle text-ink font-semibold shadow-2xs'
                  : 'text-muted hover:text-ink'
              }`}
              title="Concentric orbits with Seeds at center radar core"
            >
              <Radio className="w-3 h-3" /> Radar
            </button>
            <button
              onClick={() => switchLayout('cose')}
              className={`px-2 py-1 rounded text-xs font-medium cursor-pointer flex items-center gap-1 transition-colors ${
                layoutMode === 'cose'
                  ? 'bg-subtle text-ink font-semibold shadow-2xs'
                  : 'text-muted hover:text-ink'
              }`}
              title="Organic force-directed spread with wide spacing"
            >
              <Layers className="w-3 h-3" /> Spread
            </button>
            <button
              onClick={() => switchLayout('timeline')}
              className={`px-2 py-1 rounded text-xs font-medium cursor-pointer flex items-center gap-1 transition-colors ${
                layoutMode === 'timeline'
                  ? 'bg-subtle text-ink font-semibold shadow-2xs'
                  : 'text-muted hover:text-ink'
              }`}
              title="Chronological timeline cascade from left to right"
            >
              <Clock className="w-3 h-3" /> Timeline
            </button>
          </div>
        </div>

        {/* Density & Isolation Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Edge Density Toggle */}
          <div className="flex items-center gap-1">
            <span className="text-muted font-medium flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-accent" /> Density:
            </span>
            <div className="inline-flex rounded-md border border-line p-0.5 bg-surface">
              <button
                onClick={() => setDensityMode('backbone')}
                className={`px-2 py-1 rounded text-xs cursor-pointer ${
                  densityMode === 'backbone'
                    ? 'bg-subtle text-ink font-semibold shadow-2xs'
                    : 'text-muted hover:text-ink'
                }`}
                title="Prunes redundant clique links to display core directional flow arrows"
              >
                Core Flow ({backboneCount})
              </button>
              <button
                onClick={() => setDensityMode('all')}
                className={`px-2 py-1 rounded text-xs cursor-pointer ${
                  densityMode === 'all'
                    ? 'bg-subtle text-ink font-semibold shadow-2xs'
                    : 'text-muted hover:text-ink'
                }`}
                title="Show all raw co-occurrence edges"
              >
                All Links ({rawCount})
              </button>
            </div>
          </div>

          {/* Campaign Isolation Filter */}
          <div className="flex items-center gap-1">
            <span className="text-muted font-medium flex items-center gap-1">
              <Filter className="w-3.5 h-3.5" /> Isolate:
            </span>
            <select
              value={isolatedCampaign}
              onChange={(e) => {
                setIsolatedCampaign(e.target.value)
                if (e.target.value !== 'all') onSelect(e.target.value)
              }}
              className="bg-surface border border-line rounded px-2 py-1 text-xs text-ink focus:outline-none focus:ring-1 focus:ring-accent"
            >
              <option value="all">All Campaigns</option>
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id.toUpperCase()} ({c.size} accs)
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main Cytoscape Canvas Container */}
      <div className="relative border border-line rounded-lg overflow-hidden bg-surface">
        <div
          ref={containerRef}
          className="h-[540px] w-full"
          aria-label="Coordination network graph"
        />

        {/* Floating Controls (Zoom & Fit) */}
        <div className="absolute top-3 right-3 flex gap-1 z-10">
          <Button
            variant="secondary"
            className="px-2 shadow-xs"
            onClick={() => zoom(1.25)}
            aria-label="Zoom in"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button
            variant="secondary"
            className="px-2 shadow-xs"
            onClick={() => zoom(0.8)}
            aria-label="Zoom out"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <Button
            variant="secondary"
            className="px-2 shadow-xs"
            onClick={() => cyRef.current?.fit(undefined, 35)}
            aria-label="Fit to screen"
            title="Fit to screen"
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
        </div>

        {/* Interactive Floating Hover Tooltip */}
        {hoveredNode && (
          <div
            className="pointer-events-none absolute z-20 bg-surface/95 backdrop-blur-xs border border-line shadow-md rounded-lg p-2.5 text-xs max-w-xs space-y-1 transform -translate-x-1/2 -translate-y-full -mt-2 transition-all"
            style={{
              left: Math.max(120, Math.min(hoveredNode.x, (containerRef.current?.clientWidth || 700) - 120)),
              top: Math.max(80, hoveredNode.y),
            }}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono font-bold text-ink truncate">
                {hoveredNode.label || `@${hoveredNode.id}`}
              </span>
              {hoveredNode.role && (
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.2 rounded uppercase ${
                    hoveredNode.role === 'seed'
                      ? 'bg-ink text-surface'
                      : hoveredNode.role === 'amplifier'
                      ? 'bg-alert-soft text-alert'
                      : 'bg-subtle text-muted'
                  }`}
                >
                  {hoveredNode.role}
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[11px] text-muted pt-1">
              <div>
                Campaign:{' '}
                <strong
                  style={{
                    color: hoveredNode.campaign ? campaignColor(hoveredNode.campaign) : undefined,
                  }}
                >
                  {hoveredNode.campaign ? hoveredNode.campaign.toUpperCase() : 'None'}
                </strong>
              </div>
              <div>
                Total Links: <strong className="text-ink">{hoveredNode.degree}</strong>
                {densityMode === 'backbone' && hoveredNode.degree > hoveredNode.visibleLinks && (
                  <span className="text-[10px] text-muted block">
                    (showing {hoveredNode.visibleLinks} in Core Flow)
                  </span>
                )}
              </div>
              {hoveredNode.first_seen && (
                <div className="col-span-2 text-[10px] text-faint">
                  First active: {fmtClock(hoveredNode.first_seen)}
                </div>
              )}
            </div>
            {densityMode === 'backbone' && hoveredNode.degree > hoveredNode.visibleLinks ? (
              <div className="text-[10px] text-accent">
                Switch to &ldquo;All Links&rdquo; above to reveal all {hoveredNode.degree} lines
              </div>
            ) : (
              <div className="text-[10px] text-accent">Connected flow arrows highlighted</div>
            )}
          </div>
        )}
      </div>

      {/* Legend & Campaign Quick Selectors */}
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 px-4 py-2.5 border border-line rounded-lg bg-surface text-xs text-muted">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <span className="font-semibold text-ink text-[11px] uppercase tracking-wider">
            Campaigns:
          </span>
          {campaigns.map((c) => (
            <button
              key={c.id}
              onClick={() => {
                onSelect(c.id)
                if (isolatedCampaign !== 'all') setIsolatedCampaign(c.id)
              }}
              className="flex items-center gap-1.5 hover:text-ink cursor-pointer transition-colors"
            >
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ background: campaignColor(c.id) }}
              />
              <span className="font-medium">{c.id.toUpperCase()}</span>
              {c.top_hashtag && (
                <span className="text-muted text-[11px] font-mono">{c.top_hashtag}</span>
              )}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px]">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-faint border-2 border-ink" /> Seed (Originator)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3.5 h-3.5 rounded-full bg-faint border-2 border-alert" /> Amplifier
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-faint" /> Member
          </span>
          <span className="flex items-center gap-1 text-accent font-medium">
            ➔ Direction of Influence
          </span>
        </div>
      </div>
    </div>
  )
}
