import { useState } from 'react'
import {
  Calendar,
  Briefcase,
  GitBranch,
  ArrowRight,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2,
  History
} from 'lucide-react'

export default function AssessmentHistoryList({
  assessments = [],
  onSelectAssessment,
  onDeleteAssessment,
  loading = false,
}) {
  const [deletingId, setDeletingId] = useState(null)

  async function handleDelete(id, e) {
    e.stopPropagation()
    if (!window.confirm('Are you sure you want to delete this saved assessment?')) {
      return
    }
    setDeletingId(id)
    try {
      await onDeleteAssessment(id)
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) {
    return (
      <div className="p-12 text-center rounded-2xl bg-[#1f1e1e] border border-[#353333] space-y-3">
        <Loader2 className="w-6 h-6 animate-spin text-[#FF8900] mx-auto" />
        <p className="text-xs text-[#8c8888]">Loading assessment history...</p>
      </div>
    )
  }

  if (!assessments || assessments.length === 0) {
    return (
      <div className="p-12 text-center rounded-2xl bg-[#1f1e1e] border border-dashed border-[#353333] space-y-3">
        <History className="w-8 h-8 text-[#8c8888] mx-auto" />
        <div>
          <h4 className="text-sm font-bold text-white">No Previous Assessments</h4>
          <p className="text-xs text-[#8c8888] mt-1">
            Run your first skill-gap assessment to track your portfolio match score over time.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {assessments.map((as) => {
        const score = as.match_score
        const reposCount = (as.selected_repository_ids || []).length
        const isDeleting = deletingId === as.id

        let scoreBadgeClass = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25'
        if (score === null || score === undefined) {
          scoreBadgeClass = 'text-zinc-400 bg-zinc-500/10 border-zinc-500/25'
        } else if (score < 50) {
          scoreBadgeClass = 'text-amber-400 bg-amber-500/10 border-amber-500/25'
        } else if (score < 75) {
          scoreBadgeClass = 'text-[#FF8900] bg-[#FF8900]/10 border-[#FF8900]/25'
        }

        const dateStr = as.completed_at || as.created_at
          ? new Date(as.completed_at || as.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })
          : 'Recent'

        return (
          <div
            key={as.id}
            onClick={() => onSelectAssessment(as.id)}
            className="p-5 rounded-2xl bg-[#1f1e1e] border border-[#353333] hover:border-[#FF8900]/50 transition-all cursor-pointer group space-y-3"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h4 className="text-base font-bold text-white tracking-tight group-hover:text-[#FF8900] transition-colors">
                    {as.job_title || 'Software Engineer'}
                  </h4>
                  <span className="text-xs text-[#8c8888]">&bull;</span>
                  <span className="text-xs text-[#b0abab]">{as.company_name || 'Employer'}</span>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-xs text-[#8c8888]">
                  <span className="flex items-center gap-1 font-mono">
                    <Calendar className="w-3.5 h-3.5 text-[#FF8900]" />
                    {dateStr}
                  </span>
                  <span>&bull;</span>
                  <span className="flex items-center gap-1">
                    <GitBranch className="w-3.5 h-3.5 text-[#FF8900]" />
                    {reposCount} {reposCount === 1 ? 'repository' : 'repositories'}
                  </span>
                </div>
              </div>

              {/* Right Side: Score Badge & Actions */}
              <div className="flex items-center gap-4">
                <div className={`px-3 py-1.5 rounded-xl border text-center font-bold text-sm ${scoreBadgeClass}`}>
                  {score !== null && score !== undefined ? `${score}% Match` : 'N/A'}
                </div>

                <button
                  type="button"
                  disabled={isDeleting}
                  onClick={(e) => handleDelete(as.id, e)}
                  className="p-2 rounded-lg text-[#8c8888] hover:text-rose-400 hover:bg-[#2b2a2a] transition-colors"
                  title="Delete assessment"
                >
                  {isDeleting ? (
                    <Loader2 className="w-4 h-4 animate-spin text-rose-400" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>

                <div className="w-8 h-8 rounded-lg bg-[#2b2a2a] border border-[#3a3838] flex items-center justify-center text-[#b0abab] group-hover:text-[#FF8900] group-hover:border-[#FF8900]/40 transition-colors">
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </div>

            {/* Counts breakdown row */}
            <div className="pt-2 border-t border-[#2e2d2d] flex flex-wrap items-center gap-4 text-xs text-[#8c8888]">
              <span className="flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <strong className="text-emerald-400">{as.demonstrated_count || 0}</strong> Demonstrated
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <strong className="text-amber-400">{as.partially_demonstrated_count || 0}</strong> Partial
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1">
                <XCircle className="w-3.5 h-3.5 text-rose-400" />
                <strong className="text-rose-400">{as.not_demonstrated_count || 0}</strong> Not Found
              </span>
              <span className="ml-auto font-mono text-[11px] text-[#6d6a6a]">
                Total: {as.total_requirements || 0} skills
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
