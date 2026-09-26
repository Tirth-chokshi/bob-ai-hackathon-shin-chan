import React from 'react'
import { Printer, ExternalLink, ShieldCheck, FileText } from 'lucide-react'

export function BriefView({ datasetId, briefUrl }) {
  const fullUrl = briefUrl || `/api/datasets/${datasetId}/brief`

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      {/* Action Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base">
              Cyber Threat Escalation Brief (Station House Officer)
            </h3>
            <p className="text-xs text-slate-400">
              Formally structured electronic evidence brief compliant with Section 63 BSA 2023.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <a
            href={fullUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Open in New Tab
          </a>

          <a
            href={fullUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all"
          >
            <Printer className="w-3.5 h-3.5" />
            Print / Save as PDF
          </a>
        </div>
      </div>

      {/* Embedded Printable Document Frame */}
      <div className="rounded-2xl border border-slate-800 bg-white shadow-2xl overflow-hidden h-[750px]">
        <iframe
          src={fullUrl}
          title="Threat Intelligence Escalation Brief"
          className="w-full h-full border-0"
        />
      </div>
    </div>
  )
}
