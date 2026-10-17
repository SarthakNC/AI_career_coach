import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Briefcase,
  GitBranch,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ArrowRight,
  ShieldCheck,
  CheckSquare,
  Square
} from 'lucide-react'

export default function AssessmentSetup({
  jobs = [],
  repositories = [],
  onStartAssessment,
  loading = false,
  error = ''
}) {
  const [selectedJobId, setSelectedJobId] = useState('')
  const [selectedRepoIds, setSelectedRepoIds] = useState([])

  // Toggle single repository selection
  function toggleRepo(repoId) {
    if (selectedRepoIds.includes(repoId)) {
      setSelectedRepoIds(selectedRepoIds.filter((id) => id !== repoId))
    } else {
      setSelectedRepoIds([...selectedRepoIds, repoId])
    }
  }

  // Select all repositories
  function selectAllRepos() {
    setSelectedRepoIds(repositories.map((r) => r.id))
  }

  // Clear repository selection
  function clearRepos() {
    setSelectedRepoIds([])
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!selectedJobId || selectedRepoIds.length === 0) return
    onStartAssessment({
      jobId: selectedJobId,
      repositoryIds: selectedRepoIds,
    })
  }

  const selectedJob = jobs.find((j) => j.id === selectedJobId)
  const canSubmit = selectedJobId && selectedRepoIds.length > 0 && !loading

  return (
    <div className="space-y-6">
      {/* Header Info Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[#FF8900]/10 via-[#272626] to-[#1f1e1e] border border-[#FF8900]/25">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-[#FF8900]/20 text-[#FF8900]">
                <Sparkles className="w-4 h-4" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">
                AI Skill-Gap Assessment
              </h2>
            </div>
            <p className="text-xs text-[#b0abab] mt-1.5 max-w-2xl leading-relaxed">
              Compare requirements extracted from real job postings against verified technical evidence
              from your analyzed GitHub repositories. Every score is explainable, deterministic, and evidence-linked.
            </p>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#141414] border border-[#353333] text-xs text-emerald-400 font-mono shrink-0">
            <ShieldCheck className="w-4 h-4" />
            
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-3">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
          <div className="space-y-1">
            <div className="font-semibold text-rose-200">Unable to Run Assessment</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Select Job Posting */}
        <div className="p-6 rounded-2xl bg-[#1f1e1e] border border-[#353333] space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-[#FF8900] text-black font-bold text-xs flex items-center justify-center">
                1
              </div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Select Analyzed Target Job
              </h3>
            </div>

            <Link
              to="/dashboard/jobs"
              className="text-xs text-[#FF8900] hover:text-[#ffa333] flex items-center gap-1 transition-colors"
            >
              <span>Analyze New Job</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {jobs.length === 0 ? (
            <div className="p-6 text-center rounded-xl bg-[#181717] border border-dashed border-[#383636] space-y-3">
              <Briefcase className="w-8 h-8 text-[#8c8888] mx-auto" />
              <div>
                <p className="text-sm font-semibold text-white">No analyzed jobs found</p>
                <p className="text-xs text-[#8c8888] mt-1">
                  You need to analyze at least one job posting before running an assessment.
                </p>
              </div>
              <Link
                to="/dashboard/jobs"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#FF8900] hover:bg-[#e07800] text-black font-semibold text-xs transition-colors"
              >
                Go to Job Analysis
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {jobs.map((job) => {
                const isSelected = selectedJobId === job.id
                return (
                  <div
                    key={job.id}
                    onClick={() => setSelectedJobId(job.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-[#FF8900]/10 border-[#FF8900] shadow-lg shadow-[#FF8900]/5'
                        : 'bg-[#262525] border-[#383636] hover:border-[#4d4a4a]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <h4 className="text-sm font-bold text-white tracking-tight line-clamp-1">
                          {job.job_title || 'Untitled Role'}
                        </h4>
                        <p className="text-xs text-[#b0abab]">
                          {job.company_name || 'Target Employer'}
                        </p>
                      </div>

                      <div className={`w-4 h-4 rounded-full border flex items-center justify-center shrink-0 mt-0.5 ${
                        isSelected
                          ? 'border-[#FF8900] bg-[#FF8900]'
                          : 'border-[#4f4d4d]'
                      }`}>
                        {isSelected && <div className="w-1.5 h-1.5 bg-black rounded-full" />}
                      </div>
                    </div>

                    <div className="mt-3 pt-2 border-t border-[#333131] flex items-center justify-between text-[11px] text-[#8c8888]">
                      <span className="font-mono text-[#FF8900]">
                        {job.requirement_count} {job.requirement_count === 1 ? 'skill extracted' : 'skills extracted'}
                      </span>
                      <span>
                        {job.created_at ? new Date(job.created_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Step 2: Select Analyzed Repositories */}
        <div className="p-6 rounded-2xl bg-[#1f1e1e] border border-[#353333] space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-[#FF8900] text-black font-bold text-xs flex items-center justify-center">
                2
              </div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Select Analyzed Repositories ({selectedRepoIds.length} selected)
              </h3>
            </div>

            <div className="flex items-center gap-3 text-xs">
              {repositories.length > 0 && (
                <>
                  <button
                    type="button"
                    onClick={selectAllRepos}
                    className="text-[#FF8900] hover:underline"
                  >
                    Select All
                  </button>
                  <span className="text-[#444]">&bull;</span>
                  <button
                    type="button"
                    onClick={clearRepos}
                    className="text-[#8c8888] hover:text-white"
                  >
                    Clear
                  </button>
                </>
              )}
              <span className="text-[#444]">&bull;</span>
              <Link
                to="/dashboard/github"
                className="text-xs text-[#FF8900] hover:text-[#ffa333] flex items-center gap-1 transition-colors"
              >
                <span>Manage Repos</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>

          {repositories.length === 0 ? (
            <div className="p-6 text-center rounded-xl bg-[#181717] border border-dashed border-[#383636] space-y-3">
              <GitBranch className="w-8 h-8 text-[#8c8888] mx-auto" />
              <div>
                <p className="text-sm font-semibold text-white">No analyzed repositories found</p>
                <p className="text-xs text-[#8c8888] mt-1">
                  You need to analyze at least one GitHub repository in GitHub Portfolio before running an assessment.
                </p>
              </div>
              <Link
                to="/dashboard/github"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#FF8900] hover:bg-[#e07800] text-black font-semibold text-xs transition-colors"
              >
                Go to GitHub Portfolio
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {repositories.map((repo) => {
                const isSelected = selectedRepoIds.includes(repo.id)
                return (
                  <div
                    key={repo.id}
                    onClick={() => toggleRepo(repo.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-[#FF8900]/10 border-[#FF8900]'
                        : 'bg-[#262525] border-[#383636] hover:border-[#4d4a4a]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <GitBranch className="w-4 h-4 text-[#FF8900]" />
                          <h4 className="text-sm font-bold text-white tracking-tight font-mono">
                            {repo.full_name || repo.name}
                          </h4>
                        </div>
                        {repo.language && (
                          <span className="text-[11px] text-[#8c8888]">
                            Primary: <strong className="text-[#b0abab]">{repo.language}</strong>
                          </span>
                        )}
                      </div>

                      <div className="mt-0.5 text-[#FF8900]">
                        {isSelected ? (
                          <CheckSquare className="w-5 h-5" />
                        ) : (
                          <Square className="w-5 h-5 text-[#4f4d4d]" />
                        )}
                      </div>
                    </div>

                    <div className="mt-3 pt-2 border-t border-[#333131] flex items-center justify-between text-[11px] text-[#8c8888]">
                      <span>
                        <strong className="text-emerald-400">{repo.evidence_count}</strong> verified evidence items
                      </span>
                      {repo.last_analyzed_commit_sha && (
                        <span className="font-mono text-[10px] text-[#6d6a6a]">
                          Commit: {repo.last_analyzed_commit_sha.substring(0, 7)}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Start Button & Guidance */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-[#1f1e1e] border border-[#353333]">
          <div className="text-xs text-[#8c8888]">
            {selectedJob ? (
              <span>
                Ready to evaluate <strong className="text-white">{selectedJob.job_title}</strong> against{' '}
                <strong className="text-white">{selectedRepoIds.length}</strong> selected{' '}
                {selectedRepoIds.length === 1 ? 'repository' : 'repositories'}.
              </span>
            ) : (
              <span>Select a target job and at least one repository to begin.</span>
            )}
          </div>

          <button
            type="submit"
            disabled={!canSubmit}
            className={`flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all ${
              canSubmit
                ? 'bg-[#FF8900] hover:bg-[#e07800] text-black shadow-lg shadow-[#FF8900]/20'
                : 'bg-[#333131] text-[#6d6a6a] cursor-not-allowed border border-[#3f3d3d]'
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Evaluating Evidence & Scoring...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Start Skill-Gap Assessment</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
