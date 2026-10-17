import { useState } from 'react'
import {
  GitBranch,
  Star,
  ExternalLink,
  Play,
  Loader2,
  Trash2,
  CheckCircle2,
  ChevronRight,
} from 'lucide-react'

export default function RepositoryList({
  repositories,
  selectedRepoId,
  onSelectRepo,
  onAnalyzeRepo,
  onDeleteRepo,
  isAnalyzingId,
}) {
  const [confirmDeleteId, setConfirmDeleteId] = useState(null)

  function handleDeleteClick(e, repoId) {
    e.stopPropagation()
    if (confirmDeleteId === repoId) {
      onDeleteRepo(repoId)
      setConfirmDeleteId(null)
    } else {
      setConfirmDeleteId(repoId)
    }
  }

  function handleCancelDelete(e) {
    e.stopPropagation()
    setConfirmDeleteId(null)
  }

  if (!repositories || repositories.length === 0) {
    return (
      <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-[#2a2929] flex items-center justify-center mx-auto mb-3">
          <GitBranch className="w-6 h-6 text-[#888]" />
        </div>
        <h3 className="text-base font-bold text-white m-0 mb-1">No Repositories in Portfolio</h3>
        <p className="text-xs text-[#888] max-w-sm mx-auto m-0">
          Enter a GitHub username or repository URL above to add public repositories to your portfolio.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {repositories.map((repo) => {
        const isSelected = repo.id === selectedRepoId
        const isAnalyzing = isAnalyzingId === repo.id
        const isConfirming = confirmDeleteId === repo.id
        const isAnalyzed = Boolean(repo.last_analyzed_commit_sha || repo.latest_analysis)

        return (
          <div
            key={repo.id}
            onClick={() => onSelectRepo(repo.id)}
            className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 ${
              isSelected
                ? 'bg-[#FF8900]/10 border-[#FF8900]/40 shadow-lg'
                : 'bg-[#1a1919] border-[#353333] hover:border-[#444]'
            }`}
          >
            <div className="min-w-0 space-y-1.5 flex-1">
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className="text-base font-bold text-white hover:text-[#FF8900] transition-colors">
                  {repo.full_name}
                </span>

                {repo.language && (
                  <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#2a2929] text-[#d4cfcf] border border-[#3a3838]">
                    {repo.language}
                  </span>
                )}

                {repo.stargazers_count > 0 && (
                  <span className="flex items-center gap-1 text-xs text-amber-400">
                    <Star className="w-3.5 h-3.5 fill-amber-400" />
                    {repo.stargazers_count}
                  </span>
                )}

                {isAnalyzed && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Analyzed
                  </span>
                )}
              </div>

              {repo.description && (
                <p className="text-xs text-[#b0abab] line-clamp-2 m-0 leading-relaxed max-w-2xl">
                  {repo.description}
                </p>
              )}

              <div className="flex items-center gap-4 text-[11px] text-[#888] pt-1">
                <span>Branch: <strong className="text-[#bbb]">{repo.default_branch}</strong></span>
                {repo.last_analyzed_commit_sha && (
                  <span>
                    Commit: <strong className="font-mono text-[#bbb]">{repo.last_analyzed_commit_sha.slice(0, 7)}</strong>
                  </span>
                )}
                <a
                  href={repo.html_url}
                  target="_blank"
                  rel="noreferrer noopener"
                  onClick={(e) => e.stopPropagation()}
                  className="inline-flex items-center gap-1 text-[#FF8900] hover:underline"
                >
                  <ExternalLink className="w-3 h-3" />
                  GitHub
                </a>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 flex-shrink-0 self-end md:self-center">
              {/* Analyze / Reanalyze Button */}
              <button
                type="button"
                disabled={isAnalyzing}
                onClick={(e) => {
                  e.stopPropagation()
                  onAnalyzeRepo(repo.id)
                }}
                className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer border-none shadow-sm ${
                  isAnalyzed
                    ? 'bg-[#2a2929] hover:bg-[#333] text-white border border-[#3a3838]'
                    : 'bg-[#FF8900] hover:bg-[#e07900] text-white'
                }`}
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    {isAnalyzed ? 'Re-analyze' : 'Analyze Repository'}
                  </>
                )}
              </button>

              {/* Delete / Confirm */}
              {isConfirming ? (
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={(e) => handleDeleteClick(e, repo.id)}
                    className="px-2.5 py-1.5 rounded-lg bg-rose-500 hover:bg-rose-600 text-[11px] font-semibold text-white cursor-pointer border-none"
                  >
                    Confirm
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelDelete}
                    className="px-2.5 py-1.5 rounded-lg bg-[#333] hover:bg-[#444] text-[11px] text-[#bbb] cursor-pointer border-none"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  title="Remove from portfolio"
                  onClick={(e) => handleDeleteClick(e, repo.id)}
                  className="p-2 rounded-xl text-[#777] hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer border-none bg-transparent"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}

              <ChevronRight className={`w-4 h-4 ${isSelected ? 'text-[#FF8900]' : 'text-[#555]'}`} />
            </div>
          </div>
        )
      })}
    </div>
  )
}
