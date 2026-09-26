import React, { useState } from 'react'
import { Upload, Database, ArrowRight, Loader2, CheckCircle2, Shield, Play } from 'lucide-react'

export function UploadPanel({ datasets, onSelectDataset, onUpload, onAnalyze, analyzing, currentDatasetId }) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleUploadSubmit = async () => {
    if (!selectedFile) return
    setUploading(true)
    setUploadError(null)
    try {
      const res = await onUpload(selectedFile)
      setSelectedFile(null)
      // Switch to newly uploaded dataset
      if (res && res.dataset_id) {
        onSelectDataset(res.dataset_id)
      }
    } catch (err) {
      setUploadError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Introduction Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/20 shadow-xl relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs tracking-wider uppercase mb-2">
            <Shield className="w-4 h-4" />
            Operational Threat Intelligence Engine
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight">
            Behavior First, Content Second: CIB Forensics for Indian Law Enforcement
          </h2>
          <p className="text-slate-300 text-sm mt-2 max-w-3xl leading-relaxed">
            Ingest social media streams to detect inauthentic coordinated behavior rings (time-synchronized posting, coordinated URL sharing, and targeted reply pile-ons) before synthesizing legal intelligence with IBM Bob under the Bharatiya Nyaya Sanhita (BNS) and Information Technology Act.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Available Pre-loaded Datasets */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Database className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-white text-base">Standard Scenario Datasets</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Ground-truth evaluated scenarios featuring background noise accounts and planted threat rings (rumour amplification, coordinated link manipulation, and harassment pile-ons).
            </p>

            <div className="space-y-3">
              {datasets && datasets.length > 0 ? (
                datasets.map((ds) => {
                  const isSelected = currentDatasetId === ds.id
                  return (
                    <div
                      key={ds.id}
                      onClick={() => onSelectDataset(ds.id)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? 'bg-indigo-950/40 border-indigo-500/60 ring-1 ring-indigo-500/30'
                          : 'bg-slate-950/50 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
                      }`}
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white text-sm">{ds.name}</span>
                          {ds.analyzed && (
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-medium border border-emerald-500/20">
                              Analyzed
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-400 mt-1 font-mono">
                          <span>{ds.posts.toLocaleString()} posts</span>
                          <span>•</span>
                          <span>{ds.accounts.toLocaleString()} accounts</span>
                          <span>•</span>
                          <span>ID: {ds.id}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {isSelected ? (
                          <CheckCircle2 className="w-5 h-5 text-indigo-400" />
                        ) : (
                          <div className="w-5 h-5 rounded-full border border-slate-700"></div>
                        )}
                      </div>
                    </div>
                  )
                })
              ) : (
                <div className="text-center py-6 text-slate-500 text-xs">No pre-loaded datasets discovered.</div>
              )}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800">
            <button
              onClick={() => onAnalyze(currentDatasetId)}
              disabled={analyzing || !currentDatasetId}
              className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-bold text-sm flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer disabled:cursor-not-allowed"
            >
              {analyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running CIB Forensics Pipeline...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run CIB Forensics on Selected Dataset
                </>
              )}
            </button>
          </div>
        </div>

        {/* Custom Upload Dropzone */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Upload className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-white text-base">Ingest Custom Stream (CSV)</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Upload raw or normalized social media posts CSV. Automatically adapts X/Twitter Information Operations archives, IRA troll datasets, or scenario CSVs.
            </p>

            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-6 text-center transition-all ${
                dragActive
                  ? 'border-indigo-500 bg-indigo-950/20'
                  : 'border-slate-700 bg-slate-950/40 hover:border-slate-600'
              }`}
            >
              <input
                type="file"
                id="file-upload"
                accept=".csv,.json"
                onChange={handleFileInput}
                className="hidden"
              />
              <label htmlFor="file-upload" className="cursor-pointer block">
                <Upload className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                <span className="text-sm font-semibold text-slate-200">
                  {selectedFile ? selectedFile.name : 'Click to select or drag CSV here'}
                </span>
                <p className="text-xs text-slate-500 mt-1">
                  Supports standard CSV schema (post_id, account_id, text, created_at, etc.)
                </p>
              </label>
            </div>

            {uploadError && (
              <div className="mt-3 p-3 rounded-lg bg-red-950/30 border border-red-800/40 text-red-400 text-xs">
                {uploadError}
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800">
            <button
              onClick={handleUploadSubmit}
              disabled={!selectedFile || uploading}
              className="w-full py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white font-semibold text-sm flex items-center justify-center gap-2 transition-all cursor-pointer disabled:cursor-not-allowed"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                  Ingesting File...
                </>
              ) : (
                <>
                  <ArrowRight className="w-4 h-4 text-slate-400" />
                  Upload & Register Dataset
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
