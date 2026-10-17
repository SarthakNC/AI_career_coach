import { useState, useEffect } from 'react'
import {
  X,
  History,
  TrendingUp,
  TrendingDown,
  GitCommit,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Calendar,
  Layers,
  Sparkles
} from 'lucide-react'
import { getAssessmentHistory } from '../services/api'

export default function AssessmentVersionModal({
  assessmentId,
  token,
  onClose,
  onSelectVersion
}) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [historyData, setHistoryData] = useState(null)

  useEffect(() => {
    async function fetchHistory() {
      if (!assessmentId || !token) return
      setLoading(true)
      setError(null)
      try {
        const data = await getAssessmentHistory(assessmentId, token)
        setHistoryData(data)
      } catch (err) {
        setError(err.message || 'Failed to load assessment version history.')
      } finally {
        setLoading(false)
      }
    }
    fetchHistory()
  }, [assessmentId, token])

  if (!assessmentId) return null

  const versions = historyData?.versions || []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#1f1e1e] border border-[#353333] rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#353333] bg-[#1a1919]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">
                {historyData?.job_title ? `${historyData.job_title} — Version History` : 'Assessment Version History'}
              </h3>
              <p className="text-xs text-[#a09e9e] mt-0.5">
                {historyData?.company_name && <span>{historyData.company_name} &bull; </span>}
                Currently at version {historyData?.current_version || 1}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#8e8a8a] hover:text-white hover:bg-[#2d2b2b] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading && (
            <div className="py-12 text-center text-sm text-[#8e8a8a]">
              <div className="w-6 h-6 border-2 border-[#FF8900] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              Loading assessment version lineage...
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
              {error}
            </div>
          )}

          {!loading && !error && versions.length === 0 && (
            <div className="py-12 text-center text-sm text-[#8e8a8a]">
              No previous version records found for this assessment.
            </div>
          )}

          {!loading && !error && versions.length > 0 && (
            <div className="space-y-4">
              <p className="text-xs text-[#a09e9e]">
                Every time new commits are automatically detected and analyzed in your GitHub portfolio,
                a new assessment snapshot is created to preserve your history and progress.
              </p>

              <div className="relative border-l-2 border-[#383636] ml-4 pl-6 space-y-6 my-4">
                {versions.map((ver, idx) => {
                  const scoreDelta = ver.score_delta || 0
                  const isPositive = scoreDelta > 0
                  const isNegative = scoreDelta < 0
                  const isCurrent = ver.id === assessmentId

                  return (
                    <div key={ver.id || idx} className="relative group">
                      {/* Timeline Dot */}
                      <div className={`absolute -left-[31px] top-1.5 w-4 h-4 rounded-full border-2 ${
                        isCurrent
                          ? 'bg-[#FF8900] border-[#1f1e1e] ring-4 ring-[#FF8900]/20'
                          : 'bg-[#383636] border-[#1f1e1e]'
                      }`} />

                      {/* Version Card */}
                      <div className={`p-4 rounded-xl border transition-all ${
                        isCurrent
                          ? 'bg-[#252323] border-[#FF8900]/40 shadow-lg'
                          : 'bg-[#212020] border-[#353333] hover:border-[#4d4a4a]'
                      }`}>
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-white">Version {ver.version || (idx + 1)}</span>
                            {isCurrent && (
                              <span className="px-2 py-0.5 text-[10px] uppercase font-bold rounded bg-[#FF8900]/15 text-[#FF8900] border border-[#FF8900]/30">
                                Current
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2">
                            {scoreDelta !== 0 && (
                              <span className={`px-2 py-0.5 rounded text-xs font-semibold flex items-center gap-1 border ${
                                isPositive
                                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                  : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                              }`}>
                                {isPositive && <TrendingUp className="w-3.5 h-3.5" />}
                                {isNegative && <TrendingDown className="w-3.5 h-3.5" />}
                                <span>{scoreDelta > 0 ? `+${scoreDelta}%` : `${scoreDelta}%`}</span>
                              </span>
                            )}

                            <span className="text-base font-bold text-white">
                              {ver.match_score !== null && ver.match_score !== undefined ? `${ver.match_score}%` : 'N/A'}
                            </span>
                          </div>
                        </div>

                        {/* Metadata row */}
                        <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-[#8e8a8a] mt-2 font-mono">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5 text-[#a09e9e]" />
                            <span>{new Date(ver.created_at).toLocaleDateString()} {new Date(ver.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          </div>

                          {ver.trigger_commit_sha && (
                            <div className="flex items-center gap-1">
                              <GitCommit className="w-3.5 h-3.5 text-amber-400" />
                              <span>Triggered by <code className="text-amber-300">{ver.trigger_commit_sha.substring(0, 7)}</code></span>
                            </div>
                          )}
                        </div>

                        {/* Breakdown pills */}
                        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-[#333131] text-xs">
                          <div className="flex items-center gap-1.5 text-emerald-400">
                            <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                            <span>{ver.demonstrated_count || 0} demonstrated</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-amber-400">
                            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                            <span>{ver.partially_demonstrated_count || 0} partial</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-[#8e8a8a]">
                            <HelpCircle className="w-3.5 h-3.5 flex-shrink-0" />
                            <span>{ver.not_demonstrated_count || 0} gap</span>
                          </div>
                        </div>

                        {/* Action */}
                        {onSelectVersion && !isCurrent && (
                          <div className="mt-3 flex justify-end">
                            <button
                              onClick={() => onSelectVersion(ver.id)}
                              className="px-3 py-1 text-xs rounded-lg bg-[#333131] hover:bg-[#3d3b3b] text-zinc-200 transition-colors"
                            >
                              Inspect this version
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-[#353333] bg-[#1a1919] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#333131] hover:bg-[#3d3b3b] text-white rounded-lg text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  )
}
