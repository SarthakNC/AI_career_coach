import { useState } from 'react'
import {
  X,
  GitCommit,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  Clock,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  ExternalLink,
  Layers,
  ArrowRight
} from 'lucide-react'

export default function ChangeEventDetailModal({
  event,
  onClose,
  onRetry,
  onOpenAssessment
}) {
  const [retrying, setRetrying] = useState(false)
  const [selectedPatchFile, setSelectedPatchFile] = useState(null)

  if (!event) return null

  const shortSha = event.detected_commit_sha ? event.detected_commit_sha.substring(0, 7) : 'Commit'
  const prevShortSha = event.previous_commit_sha ? event.previous_commit_sha.substring(0, 7) : null

  const statusColors = {
    completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    processing: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    pending: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    failed: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    skipped: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
  }

  const fileStatusColors = {
    added: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    modified: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    removed: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    renamed: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  }

  async function handleRetryClick() {
    if (!onRetry || retrying) return
    setRetrying(true)
    try {
      await onRetry(event.id)
    } finally {
      setRetrying(false)
    }
  }

  const summary = event.evidence_change_summary || {}
  const assessmentUpdates = event.assessment_updates || []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#1f1e1e] border border-[#353333] rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#353333] bg-[#1a1919]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#FF8900]/10 border border-[#FF8900]/30 flex items-center justify-center text-[#FF8900]">
              <GitCommit className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white">{event.repository_name}</h3>
                <span className={`px-2.5 py-0.5 text-xs font-medium rounded-full border ${statusColors[event.status] || statusColors.pending}`}>
                  {event.status}
                </span>
              </div>
              <p className="text-xs text-[#a09e9e] mt-0.5">
                Commit <code className="bg-[#2d2b2b] px-1.5 py-0.5 rounded text-amber-300 font-mono">{shortSha}</code>
                {prevShortSha && (
                  <span> (replaces <code className="bg-[#2d2b2b] px-1 py-0.5 rounded text-[#8e8a8a] font-mono">{prevShortSha}</code>)</span>
                )}
                {event.commit_author && <span> &bull; by {event.commit_author}</span>}
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

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">

          {/* Commit Message Box */}
          {event.commit_message && (
            <div className="bg-[#282626] border border-[#3d3b3b] rounded-xl p-4">
              <span className="text-xs uppercase tracking-wider text-[#8e8a8a] font-semibold block mb-1">Commit Message</span>
              <p className="text-sm text-zinc-200 font-mono whitespace-pre-wrap">{event.commit_message}</p>
            </div>
          )}

          {/* Error Banner if failed */}
          {event.status === 'failed' && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-rose-400">Processing Failed</h4>
                  <p className="text-xs text-rose-200/80 mt-1">{event.last_error || 'An unexpected error occurred during change reconciliation.'}</p>
                </div>
              </div>
              {onRetry && (
                <button
                  onClick={handleRetryClick}
                  disabled={retrying}
                  className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${retrying ? 'animate-spin' : ''}`} />
                  <span>{retrying ? 'Retrying...' : 'Retry Event'}</span>
                </button>
              )}
            </div>
          )}

          {/* Evidence Impact Summary Cards */}
          <div>
            <h4 className="text-xs uppercase tracking-wider text-[#8e8a8a] font-semibold mb-3 flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#FF8900]" />
              Evidence Reconciliation Impact
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-[#252424] border border-[#383636] rounded-xl p-3.5">
                <div className="text-xs text-[#a09e9e]">Changed Files</div>
                <div className="text-xl font-bold text-white mt-1">{event.changed_files_count || 0}</div>
              </div>
              <div className="bg-[#252424] border border-[#383636] rounded-xl p-3.5">
                <div className="text-xs text-[#a09e9e]">Evidence Extracted</div>
                <div className="text-xl font-bold text-emerald-400 mt-1">+{summary.added_count || 0}</div>
              </div>
              <div className="bg-[#252424] border border-[#383636] rounded-xl p-3.5">
                <div className="text-xs text-[#a09e9e]">Removed / Stale</div>
                <div className="text-xl font-bold text-rose-400 mt-1">-{summary.invalidated_count || 0}</div>
              </div>
              <div className="bg-[#252424] border border-[#383636] rounded-xl p-3.5">
                <div className="text-xs text-[#a09e9e]">Assessments Updated</div>
                <div className="text-xl font-bold text-[#FF8900] mt-1">{event.assessments_recalculated_count || 0}</div>
              </div>
            </div>

            {/* Affected Skills Chips */}
            {summary.skills_affected && summary.skills_affected.length > 0 && (
              <div className="mt-3 bg-[#252424] border border-[#383636] rounded-xl p-3.5">
                <span className="text-xs text-[#a09e9e] block mb-2 font-medium">Reconciled Skills:</span>
                <div className="flex flex-wrap gap-1.5">
                  {summary.skills_affected.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 text-xs rounded-md bg-[#333131] text-amber-200 border border-[#444242]"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Assessment Recalculation Results */}
          {assessmentUpdates.length > 0 && (
            <div>
              <h4 className="text-xs uppercase tracking-wider text-[#8e8a8a] font-semibold mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                Updated Job Assessments
              </h4>
              <div className="space-y-2.5">
                {assessmentUpdates.map((update, idx) => {
                  const delta = update.score_delta || 0
                  const isPositive = delta > 0
                  const isNegative = delta < 0
                  return (
                    <div
                      key={idx}
                      className="bg-[#252424] border border-[#383636] rounded-xl p-4 flex items-center justify-between gap-4 hover:border-[#4d4a4a] transition-colors"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <h5 className="text-sm font-semibold text-white">{update.job_title}</h5>
                          <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#333131] text-amber-300 border border-[#444242]">
                            v{update.new_version || 2}
                          </span>
                        </div>
                        <p className="text-xs text-[#8e8a8a] mt-1">
                          Previous score: <span className="text-zinc-300">{update.previous_score ?? 'N/A'}%</span>
                          <span className="mx-2">&rarr;</span>
                          New score: <span className="text-white font-medium">{update.new_score ?? 'N/A'}%</span>
                        </p>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 border ${
                          isPositive
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : isNegative
                            ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                            : 'bg-zinc-500/10 text-zinc-300 border-zinc-500/30'
                        }`}>
                          {isPositive && <TrendingUp className="w-3.5 h-3.5" />}
                          {isNegative && <TrendingDown className="w-3.5 h-3.5" />}
                          <span>{delta > 0 ? `+${delta}%` : `${delta}%`}</span>
                        </div>

                        {onOpenAssessment && (
                          <button
                            onClick={() => onOpenAssessment(update.assessment_id)}
                            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[#333131] hover:bg-[#3f3d3d] text-zinc-200 transition-colors flex items-center gap-1.5"
                          >
                            <span>View Assessment</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Changed Files Table */}
          <div>
            <h4 className="text-xs uppercase tracking-wider text-[#8e8a8a] font-semibold mb-3 flex items-center gap-2">
              <FileCode className="w-4 h-4 text-[#FF8900]" />
              Changed Files in this Commit ({event.changed_files ? event.changed_files.length : 0})
            </h4>

            {(!event.changed_files || event.changed_files.length === 0) ? (
              <p className="text-xs text-[#8e8a8a] italic">No file-level diff recorded for this commit.</p>
            ) : (
              <div className="border border-[#383636] rounded-xl overflow-hidden divide-y divide-[#333131] bg-[#1a1919]">
                {event.changed_files.map((file, idx) => (
                  <div key={idx} className="p-3 hover:bg-[#232222] transition-colors">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className={`px-2 py-0.5 text-[11px] font-mono rounded border uppercase ${fileStatusColors[file.status] || fileStatusColors.modified}`}>
                          {file.status}
                        </span>
                        <span className="text-xs font-mono text-zinc-200 truncate">{file.filename}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs font-mono flex-shrink-0">
                        {file.additions > 0 && <span className="text-emerald-400">+{file.additions}</span>}
                        {file.deletions > 0 && <span className="text-rose-400">-{file.deletions}</span>}
                        {file.patch && (
                          <button
                            onClick={() => setSelectedPatchFile(selectedPatchFile === file.filename ? null : file.filename)}
                            className="text-xs text-amber-400 hover:underline ml-2"
                          >
                            {selectedPatchFile === file.filename ? 'Hide diff' : 'View diff'}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Expandable Patch Diff */}
                    {selectedPatchFile === file.filename && file.patch && (
                      <div className="mt-2.5 p-3 rounded-lg bg-[#141414] border border-[#2d2b2b] text-[11px] font-mono text-zinc-300 overflow-x-auto whitespace-pre max-h-48">
                        {file.patch}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-[#353333] bg-[#1a1919] flex items-center justify-between text-xs text-[#8e8a8a]">
          <div>
            Detected at {new Date(event.detected_at).toLocaleString()}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#333131] hover:bg-[#3d3b3b] text-white rounded-lg font-medium transition-colors"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  )
}
