import React from 'react'
import { VerdictCard } from './VerdictCard'
import { X, Hash, Users, Clock, Flame, ShieldAlert } from 'lucide-react'

export function CampaignPanel({
  campaign,
  verdictData,
  verdictLoading,
  onClassify,
  onClose,
}) {
  if (!campaign) {
    return (
      <div className="p-8 text-center text-slate-500 text-sm bg-slate-900/40 rounded-2xl border border-slate-800">
        Select a campaign cluster to inspect its forensic profile, feature contribution, and IBM Bob classification.
      </div>
    )
  }

  const featureLabels = {
    speed: { label: 'Temporal Velocity', max: 25 },
    duplication: { label: 'Lexical Overlap', max: 25 },
    multi_signal: { label: 'Multi-Signal Fusion', max: 15 },
    fresh_accounts: { label: 'Account Freshness', max: 15 },
    burst: { label: 'Activity Burst Ratio', max: 10 },
    concentration: { label: 'Entity Concentration', max: 10 },
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg">
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-lg font-mono font-black text-sm bg-indigo-600 text-white">
              {campaign.id.toUpperCase()}
            </span>
            <span className="text-base font-bold text-white">Forensic Investigation</span>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="text-slate-500 block text-[10px]">CIB RISK</span>
            <span className="text-white font-bold text-sm">{campaign.score}/100</span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="text-slate-500 block text-[10px]">ACCOUNTS</span>
            <span className="text-white font-bold text-sm">{campaign.size}</span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="text-slate-500 block text-[10px]">HASHTAG</span>
            <span className="text-indigo-400 font-bold text-xs truncate block">{campaign.top_hashtag || 'None'}</span>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <span className="text-slate-500 block text-[10px]">MEDIAN AGE</span>
            <span className="text-white font-bold text-xs">
              {campaign.median_account_age_days !== null ? `${campaign.median_account_age_days}d` : 'Unknown'}
            </span>
          </div>
        </div>
      </div>

      {/* Why Flagged — Feature Contribution Bars */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Why Flagged (Explainable Feature Attribution)
          </h4>
          <span className="text-[11px] font-mono text-indigo-400">Sum = {campaign.score} pts</span>
        </div>

        <div className="space-y-2.5">
          {Object.entries(campaign.features || {}).map(([featKey, points]) => {
            const meta = featureLabels[featKey] || { label: featKey, max: 25 }
            const pct = Math.min(100, Math.round((points / meta.max) * 100))
            return (
              <div key={featKey} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium">{meta.label}</span>
                  <span className="font-mono text-slate-400">
                    <strong className="text-white">{points}</strong> / {meta.max} pts
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-500"
                    style={{ width: `${pct}%` }}
                  ></div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* IBM Bob AI Verdict & Escalation */}
      <VerdictCard
        verdictData={verdictData}
        loading={verdictLoading}
        onClassify={onClassify}
        campaignId={campaign.id}
      />

      {/* Sample Evidence Posts */}
      {campaign.sample_posts && campaign.sample_posts.length > 0 && (
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Sample Forensic Evidence ({campaign.sample_posts.length} posts)
            </h4>
            <span className="text-[10px] text-slate-500 font-mono">Oldest first</span>
          </div>

          <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
            {campaign.sample_posts.map((post) => (
              <div
                key={post.post_id}
                className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs space-y-1 hover:border-slate-700 transition-all"
              >
                <div className="flex items-center justify-between font-mono text-[11px]">
                  <span className="font-bold text-indigo-400">{post.username}</span>
                  <span className="text-slate-500">
                    {new Date(post.created_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                </div>
                <p className="text-slate-200 leading-relaxed font-sans">{post.text}</p>
                <div className="text-[10px] font-mono text-slate-600">ID: {post.post_id}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
