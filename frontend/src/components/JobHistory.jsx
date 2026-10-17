import { useState } from 'react'
import { Briefcase, Building, Calendar, Trash2, ArrowRight, Loader2, Sparkles } from 'lucide-react'

export default function JobHistory({ jobs, activeJobId, onSelectJob, onDeleteJob }) {
  const [deletingId, setDeletingId] = useState(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState(null)

  async function handleDeleteClick(e, jobId) {
    e.stopPropagation()
    if (confirmDeleteId === jobId) {
      setDeletingId(jobId)
      try {
        await onDeleteJob(jobId)
      } finally {
        setDeletingId(null)
        setConfirmDeleteId(null)
      }
    } else {
      setConfirmDeleteId(jobId)
    }
  }

  function handleCancelDelete(e) {
    e.stopPropagation()
    setConfirmDeleteId(null)
  }

  if (!jobs || jobs.length === 0) {
    return (
      <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-6 text-center">
        <div className="w-10 h-10 rounded-full bg-[#2a2929] flex items-center justify-center mx-auto mb-3">
          <Sparkles className="w-5 h-5 text-[#888]" />
        </div>
        <h3 className="text-sm font-semibold text-white m-0 mb-1">No Saved Analyses Yet</h3>
        <p className="text-xs text-[#888] m-0 max-w-xs mx-auto">
          Analyze a job posting URL or paste a description to build your requirement history.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2 m-0">
          <Briefcase className="w-4 h-4 text-[#FF8900]" />
          Saved Job Analyses
        </h3>
        <span className="text-xs text-[#888] bg-[#2a2929] px-2 py-0.5 rounded-full border border-[#3a3838]">
          {jobs.length} total
        </span>
      </div>

      <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
        {jobs.map((job) => {
          const isActive = job.id === activeJobId
          const isConfirming = confirmDeleteId === job.id
          const isDeleting = deletingId === job.id
          const formattedDate = new Date(job.created_at).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          })

          return (
            <div
              key={job.id}
              onClick={() => onSelectJob(job.id)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                isActive
                  ? 'bg-[#FF8900]/10 border-[#FF8900]/40 text-white shadow'
                  : 'bg-[#232222] border-[#333131] hover:border-[#444] text-[#d4cfcf]'
              }`}
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-white truncate m-0">
                    {job.job_title || 'Untitled Role'}
                  </h4>
                  {job.company_name && (
                    <span className="text-xs text-[#888] truncate flex items-center gap-1">
                      <Building className="w-3 h-3 text-[#666]" />
                      {job.company_name}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3 mt-1.5 text-[11px] text-[#888]">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-[#666]" />
                    {formattedDate}
                  </span>
                  <span>•</span>
                  <span className="text-[#FF8900] font-medium">
                    {job.requirement_count ?? job.requirements?.length ?? 0} skills
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-1.5 flex-shrink-0">
                {isConfirming ? (
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      disabled={isDeleting}
                      onClick={(e) => handleDeleteClick(e, job.id)}
                      className="px-2 py-1 rounded-lg bg-rose-500 hover:bg-rose-600 text-[11px] font-semibold text-white transition-colors cursor-pointer border-none"
                    >
                      {isDeleting ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Confirm'}
                    </button>
                    <button
                      type="button"
                      disabled={isDeleting}
                      onClick={handleCancelDelete}
                      className="px-2 py-1 rounded-lg bg-[#333] hover:bg-[#444] text-[11px] text-[#bbb] transition-colors cursor-pointer border-none"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      title="Delete analysis"
                      onClick={(e) => handleDeleteClick(e, job.id)}
                      className="p-1.5 rounded-lg text-[#666] hover:text-rose-400 hover:bg-rose-500/10 transition-colors bg-transparent border-none cursor-pointer"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <ArrowRight className={`w-4 h-4 ${isActive ? 'text-[#FF8900]' : 'text-[#555]'}`} />
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
