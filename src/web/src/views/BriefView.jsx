import React, { useRef, useState, useEffect } from 'react'
import { ExternalLink, Printer, FileText } from 'lucide-react'
import { api } from '../api'
import { Button, Spinner, Badge } from '../ui'

/**
 * Dedicated Document Brief Viewer
 * Renders the official Section 63 BSA threat escalation brief / PDF dossier
 * with campaign scope selection, new tab viewing, and direct printing.
 */
export function BriefView({
  dataset,
  campaigns = [],
  selectedCampaignId = null,
  onSelectCampaign = () => {},
  url,
}) {
  const frameRef = useRef(null)
  const [activeCid, setActiveCid] = useState(selectedCampaignId)
  const [loading, setLoading] = useState(true)

  // Keep activeCid in sync if external selection changes
  useEffect(() => {
    if (selectedCampaignId !== undefined) {
      setActiveCid(selectedCampaignId)
    }
  }, [selectedCampaignId])

  const handleCampaignChange = (cid) => {
    setActiveCid(cid || null)
    setLoading(true)
    if (onSelectCampaign) {
      onSelectCampaign(cid || null)
    }
  }

  // Determine current brief URL (specific campaign or consolidated dossier)
  const targetUrl = activeCid
    ? api.briefUrl(dataset?.id || '', activeCid)
    : url || (dataset ? api.briefUrl(dataset.id) : '')

  const handlePrint = () => {
    if (frameRef.current?.contentWindow) {
      frameRef.current.contentWindow.print()
    } else {
      const w = window.open(targetUrl, '_blank')
      if (w) {
        w.onload = () => w.print()
      }
    }
  }

  return (
    <div className="space-y-4">
      {/* Document Brief Toolbar */}
      <div className="bg-surface border border-line rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold text-ink flex items-center gap-2">
              <FileText className="w-5 h-5 text-accent" />
              Executive Threat Escalation Brief
            </h1>
            <Badge tone="accent">Section 63 BSA Compliant</Badge>
          </div>
          <p className="text-xs text-muted mt-1">
            Official Cyber Cell Dossier · Cryptographic SHA-256 chain of custody · Formatted for court submission & SHO escalation
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          {/* Campaign Scope Dropdown */}
          {campaigns && campaigns.length > 0 && (
            <div className="flex items-center gap-1.5">
              <label htmlFor="brief-campaign-select" className="text-xs font-medium text-muted">
                Scope:
              </label>
              <select
                id="brief-campaign-select"
                value={activeCid || ''}
                onChange={(e) => handleCampaignChange(e.target.value || null)}
                className="h-8 pl-2.5 pr-8 py-1 bg-surface border border-line rounded-md text-xs font-medium text-ink cursor-pointer focus-visible:outline-2 focus-visible:outline-accent"
              >
                <option value="">Consolidated Brief (All {campaigns.length} Campaigns)</option>
                {campaigns.map((c) => {
                  const score = Math.round(c.score || 0)
                  const assessment = c.assessment?.threat_level || (score >= 70 ? 'HIGH' : 'EVAL')
                  return (
                    <option key={c.id} value={c.id}>
                      Campaign {c.id.toUpperCase()} · Score: {score}/100 [{assessment}]
                    </option>
                  )
                })}
              </select>
            </div>
          )}

          <Button
            onClick={() => window.open(targetUrl, '_blank', 'noopener')}
            title="Open printable brief document in a new tab"
          >
            <ExternalLink className="w-4 h-4" />
            Open Document
          </Button>

          <Button
            variant="primary"
            onClick={handlePrint}
            title="Print or save document as PDF"
          >
            <Printer className="w-4 h-4" />
            Print / Save PDF
          </Button>
        </div>
      </div>

      {/* Brief Document Preview Container */}
      <div className="relative bg-surface border border-line rounded-xl overflow-hidden shadow-xs">
        <div className="flex items-center justify-between px-4 py-2 bg-subtle border-b border-line text-xs text-muted">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-accent animate-pulse" />
            <span>
              Document Scope:{' '}
              <strong className="text-ink font-semibold">
                {activeCid
                  ? `Campaign ${activeCid.toUpperCase()} Single-Threat Brief`
                  : `Master Executive Threat Brief (${campaigns.length} Campaigns)`}
              </strong>
            </span>
          </div>
          {activeCid && (
            <button
              onClick={() => handleCampaignChange(null)}
              className="text-accent cursor-pointer hover:underline font-medium"
            >
              Switch to Consolidated Brief
            </button>
          )}
        </div>

        {loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-sm text-muted bg-surface/90 z-10 backdrop-blur-[1px]">
            <Spinner />
            <span>Rendering official Section 63 BSA threat escalation brief…</span>
          </div>
        )}

        <iframe
          ref={frameRef}
          key={targetUrl}
          src={targetUrl}
          title="Executive Cyber Threat Escalation Brief"
          onLoad={() => setLoading(false)}
          className="block w-full h-[calc(100vh-210px)] min-h-[720px] bg-white border-0"
        />
      </div>
    </div>
  )
}
