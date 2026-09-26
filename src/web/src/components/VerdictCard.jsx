import React from 'react'
import { ShieldAlert, AlertTriangle, Scale, CheckCircle2, Clock, DollarSign, Check, ExternalLink } from 'lucide-react'

export function VerdictCard({ verdictData, loading, onClassify, campaignId }) {
  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 text-center animate-pulse space-y-3">
        <div className="w-8 h-8 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <div className="text-sm font-bold text-indigo-300">IBM Bob AI is Analyzing Coordinated Campaign...</div>
        <p className="text-xs text-slate-400 max-w-sm mx-auto">
          Synthesizing behavioral patterns, extracting narrative targets, and mapping Indian penal provisions (~10 s).
        </p>
      </div>
    )
  }

  if (!verdictData) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-4">
        <div className="w-10 h-10 rounded-full bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center mx-auto text-indigo-400">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div>
          <h4 className="font-bold text-white text-sm">IBM Bob Threat Classification</h4>
          <p className="text-xs text-slate-400 mt-1 max-w-xs mx-auto">
            Classify threat vector, identify targets, detect physical mobilization risks, and recommend legal statutes.
          </p>
        </div>
        <button
          onClick={() => onClassify(campaignId)}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs tracking-wide uppercase shadow-lg shadow-indigo-500/20 transition-all cursor-pointer flex items-center gap-2 mx-auto"
        >
          <ShieldAlert className="w-4 h-4" />
          Ask IBM Bob
        </button>
      </div>
    )
  }

  const { verdict, escalation, cached, cost } = verdictData
  const level = escalation?.level || 'MONITOR'
  const isUrgent = level === 'URGENT'
  const isAlert = level === 'ALERT'

  const levelColor = isUrgent
    ? 'bg-red-500/10 text-red-400 border-red-500/30'
    : isAlert
    ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
    : 'bg-slate-700/20 text-slate-300 border-slate-700'

  return (
    <div className="space-y-4 rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xl">
      {/* Header & Badges */}
      <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-4 flex-wrap">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Automated Threat Classification
          </span>
          <div className="text-base font-extrabold text-white flex items-center gap-2">
            <span>{verdict.threat_type.replace('_', ' ').toUpperCase()}</span>
            <span className="text-xs font-mono font-normal text-slate-400">
              · Severity {verdict.severity}/5
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {cached && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
              Cached Verdict
            </span>
          )}
          {cost !== undefined && cost > 0 && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-950/60 text-indigo-400 border border-indigo-800/60 flex items-center gap-1">
              <DollarSign className="w-3 h-3" />
              {cost.toFixed(3)} coins
            </span>
          )}
          <span className={`px-3 py-1 rounded-full text-xs font-black tracking-wider border ${levelColor}`}>
            {level}
          </span>
        </div>
      </div>

      {/* Target & Narrative */}
      <div className="space-y-2 text-xs">
        <div>
          <span className="font-semibold text-slate-400">Target Focus:</span>
          <p className="text-slate-200 mt-0.5">{verdict.target}</p>
        </div>
        <div>
          <span className="font-semibold text-slate-400">Identified Narrative:</span>
          <p className="text-slate-300 mt-0.5 leading-relaxed">{verdict.narrative}</p>
        </div>
      </div>

      {/* Real World Call to Action Alert */}
      {verdict.offline_call_to_action && (
        <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/40 text-red-200 text-xs flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>
            <strong>Physical Mobilization Alert:</strong> Detected time or location specified for public gathering/protest.
          </span>
        </div>
      )}

      {/* Legal Suggestions */}
      {verdict.legal_suggestions && verdict.legal_suggestions.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Scale className="w-3.5 h-3.5 text-indigo-400" />
              Applicable Legal Sections
            </span>
            <span className="text-[10px] text-amber-400/90 font-medium">Verify with legal officer</span>
          </div>

          <div className="space-y-2">
            {verdict.legal_suggestions.map((sug) => (
              <div
                key={sug.id}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-indigo-300">
                    {sug.law || sug.id} <span className="text-slate-500 font-normal">({sug.ipc || 'IPC'})</span>
                  </span>
                  <span className="text-[11px] text-slate-400 italic">{sug.title}</span>
                </div>
                <p className="text-slate-300 text-[11px] leading-relaxed">{sug.why}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Escalation Directives */}
      {escalation && escalation.actions && (
        <div className="space-y-2 pt-2 border-t border-slate-800">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Operational Response Directives
          </span>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {escalation.actions.map((act, i) => (
              <li key={i} className="flex items-start gap-2">
                <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>{act}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Evidence Post IDs */}
      {verdict.evidence_post_ids && (
        <div className="pt-2 border-t border-slate-800 flex items-center gap-2 flex-wrap">
          <span className="text-[11px] font-semibold text-slate-400">Cited Evidence:</span>
          {verdict.evidence_post_ids.map((pid) => (
            <span
              key={pid}
              className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-800 text-slate-300 border border-slate-700"
            >
              {pid}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
