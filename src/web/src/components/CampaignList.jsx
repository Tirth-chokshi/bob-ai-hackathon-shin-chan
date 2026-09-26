import React from 'react'
import { AlertCircle, ArrowUpRight, Clock, Users, Hash } from 'lucide-react'

export function CampaignList({ campaigns, onSelectCampaign, selectedCampaignId }) {
  if (!campaigns || campaigns.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/40 rounded-2xl border border-slate-800 text-slate-500 text-sm">
        No coordinated campaigns detected. Run analysis from the Ingestion tab.
      </div>
    )
  }

  const getScoreBadge = (score) => {
    if (score >= 80) {
      return 'bg-red-500/10 text-red-400 border-red-500/30'
    } else if (score >= 60) {
      return 'bg-amber-500/10 text-amber-400 border-amber-500/30'
    }
    return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
  }

  const getSignalBadge = (sig) => {
    const labels = {
      co_tweet: 'Time Synced',
      co_similar_tweet: 'Lexical Match',
      co_link: 'Common URL',
      co_reply: 'Reply Burst',
      co_retweet: 'Co-Retweet',
    }
    return labels[sig] || sig
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-bold text-white text-base">Flagged Coordination Clusters</h3>
          <p className="text-xs text-slate-400">
            Ranked by explainable multi-signal CIB risk score (0–100)
          </p>
        </div>
        <span className="text-xs font-mono text-slate-500">
          {campaigns.length} cluster(s) isolated
        </span>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {campaigns.map((camp) => {
          const isSelected = selectedCampaignId === camp.id
          return (
            <div
              key={camp.id}
              onClick={() => onSelectCampaign(camp.id)}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                isSelected
                  ? 'bg-slate-850 border-indigo-500 ring-1 ring-indigo-500/40 shadow-lg shadow-indigo-500/10'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-850'
              }`}
            >
              {/* Campaign Basic Info */}
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2 py-0.5 rounded font-mono font-bold text-xs bg-slate-800 text-slate-200 border border-slate-700">
                    {camp.id.toUpperCase()}
                  </span>
                  {camp.top_hashtag && (
                    <span className="flex items-center gap-1 text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded border border-indigo-500/20">
                      <Hash className="w-3 h-3" />
                      {camp.top_hashtag.replace('#', '')}
                    </span>
                  )}
                  <span className="flex items-center gap-1 text-xs text-slate-400 font-mono">
                    <Users className="w-3 h-3 text-slate-500" />
                    {camp.size} accounts
                  </span>
                  {camp.median_account_age_days !== null && (
                    <span className="flex items-center gap-1 text-xs text-slate-400 font-mono">
                      <Clock className="w-3 h-3 text-slate-500" />
                      ~{camp.median_account_age_days}d old
                    </span>
                  )}
                </div>

                {/* Behavioral signals */}
                <div className="flex items-center gap-1.5 flex-wrap pt-1">
                  {camp.signals.map((sig) => (
                    <span
                      key={sig}
                      className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-950/80 text-slate-300 border border-slate-800"
                    >
                      {getSignalBadge(sig)}
                    </span>
                  ))}
                </div>
              </div>

              {/* Score and CTA */}
              <div className="flex items-center justify-between md:justify-end gap-4 shrink-0">
                <div className="text-right">
                  <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
                    CIB Score
                  </div>
                  <div
                    className={`inline-block px-3 py-1 rounded-lg text-sm font-black font-mono border ${getScoreBadge(
                      camp.score
                    )}`}
                  >
                    {camp.score}/100
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onSelectCampaign(camp.id)
                  }}
                  className="px-3 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-semibold flex items-center gap-1 transition-all"
                >
                  Inspect
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
