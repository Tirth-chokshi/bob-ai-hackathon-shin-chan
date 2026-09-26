import React from 'react'
import { FileText, Users, Network, AlertOctagon } from 'lucide-react'

export function StatTiles({ postsCount, accountsCount, campaignsCount, maxScore }) {
  const stats = [
    {
      label: 'Ingested Posts',
      value: (postsCount || 0).toLocaleString(),
      desc: 'Normalized multi-platform posts',
      icon: FileText,
      color: 'from-blue-500/20 to-blue-600/10',
      border: 'border-blue-500/30',
      iconColor: 'text-blue-400',
    },
    {
      label: 'Monitored Accounts',
      value: (accountsCount || 0).toLocaleString(),
      desc: 'Extracted author nodes',
      icon: Users,
      color: 'from-cyan-500/20 to-cyan-600/10',
      border: 'border-cyan-500/30',
      iconColor: 'text-cyan-400',
    },
    {
      label: 'Coordinated Rings',
      value: campaignsCount || 0,
      desc: 'Louvain modularity clusters',
      icon: Network,
      color: 'from-purple-500/20 to-purple-600/10',
      border: 'border-purple-500/30',
      iconColor: 'text-purple-400',
    },
    {
      label: 'Peak CIB Risk Score',
      value: `${maxScore || 0}/100`,
      desc: 'Behavioral coordination index',
      icon: AlertOctagon,
      color: (maxScore || 0) >= 80 ? 'from-red-500/20 to-red-600/10' : 'from-amber-500/20 to-amber-600/10',
      border: (maxScore || 0) >= 80 ? 'border-red-500/40' : 'border-amber-500/40',
      iconColor: (maxScore || 0) >= 80 ? 'text-red-400' : 'text-amber-400',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {stats.map((stat, idx) => {
        const Icon = stat.icon
        return (
          <div
            key={idx}
            className={`p-5 rounded-xl bg-slate-900/60 border ${stat.border} relative overflow-hidden backdrop-blur-sm`}
          >
            <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl ${stat.color} rounded-bl-full pointer-events-none`}></div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {stat.label}
              </span>
              <Icon className={`w-5 h-5 ${stat.iconColor}`} />
            </div>
            <div className="text-2xl font-black text-white tracking-tight mb-1 font-mono">
              {stat.value}
            </div>
            <p className="text-xs text-slate-400">{stat.desc}</p>
          </div>
        )
      })}
    </div>
  )
}
