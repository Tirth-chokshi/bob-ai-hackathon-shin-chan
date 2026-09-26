import React from 'react'
import { ShieldAlert, Cpu, CheckCircle2, AlertTriangle, FileText, Share2, BarChart3, Upload } from 'lucide-react'

export function Navbar({ activeTab, setActiveTab, bobConfigured, selectedDataset }) {
  const tabs = [
    { id: 'upload', label: 'Data Ingestion', icon: Upload },
    { id: 'overview', label: 'Forensic Overview', icon: BarChart3 },
    { id: 'network', label: 'Coordination Graph', icon: Share2 },
    { id: 'brief', label: 'Escalation Brief', icon: FileText },
  ]

  return (
    <header className="bg-slate-900/90 border-b border-slate-800 sticky top-0 z-50 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 ring-1 ring-white/20">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold tracking-tight text-white text-lg">SHIN-CHAN</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Track 2 · Cyber Forensics
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Social Media Threat Intelligence Engine</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800/80">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            )
          })}
        </nav>

        {/* Status Indicators */}
        <div className="flex items-center gap-3">
          {selectedDataset && (
            <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/80 text-xs font-mono text-slate-300 border border-slate-700">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              {selectedDataset}
            </div>
          )}

          <div
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
              bobConfigured
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>{bobConfigured ? 'IBM Bob Active' : 'Bob Cached Only'}</span>
          </div>
        </div>
      </div>
    </header>
  )
}
