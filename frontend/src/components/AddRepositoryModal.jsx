import { useState } from 'react'
import { Search, GitBranch, Plus, Check, Loader2, AlertCircle } from 'lucide-react'

export default function AddRepositoryModal({ onResolve, onAddRepo, isResolving, isOpen, onClose }) {
  const [query, setQuery] = useState('')
  const [resolvedResult, setResolvedResult] = useState(null)
  const [addingName, setAddingName] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')

  if (!isOpen) return null

  async function handleSearch(e) {
    e.preventDefault()
    if (!query.trim()) return
    setErrorMsg('')
    setResolvedResult(null)

    try {
      const data = await onResolve(query.trim())
      setResolvedResult(data)
    } catch (err) {
      setErrorMsg(err.message || 'Failed to resolve repository or user.')
    }
  }

  async function handleAdd(repo) {
    setAddingName(repo.full_name)
    setErrorMsg('')
    try {
      await onAddRepo(repo)
      // Remove from list or show added
      if (resolvedResult?.type === 'user') {
        setResolvedResult((prev) => ({
          ...prev,
          repositories: prev.repositories.map((r) =>
            r.full_name === repo.full_name ? { ...r, _added: true } : r
          ),
        }))
      } else {
        onClose()
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to add repository.')
    } finally {
      setAddingName(null)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="bg-[#1a1919] border border-[#353333] rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-6 border-b border-[#353333] flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white m-0">Add GitHub Repositories</h3>
            <p className="text-xs text-[#888] mt-1 m-0">
              Enter a GitHub username or public repository URL to import into your portfolio.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-[#888] hover:text-white text-sm bg-transparent border-none cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Search input */}
        <div className="p-6 pb-4">
          <form onSubmit={handleSearch} className="flex gap-2.5">
            <div className="relative flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. 'octocat' or 'https://github.com/facebook/react'"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#232222] border border-[#3a3838] text-sm text-white placeholder-[#777] focus:outline-none focus:border-[#FF8900]"
              />
              <Search className="w-4 h-4 text-[#888] absolute left-3.5 top-3" />
            </div>
            <button
              type="submit"
              disabled={isResolving || !query.trim()}
              className="px-5 py-2.5 rounded-xl bg-[#FF8900] hover:bg-[#e07900] disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-2 cursor-pointer border-none transition-all shadow-md"
            >
              {isResolving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Resolve'}
            </button>
          </form>

          {errorMsg && (
            <div className="mt-3 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}
        </div>

        {/* Resolved Results list */}
        <div className="p-6 pt-0 flex-1 overflow-y-auto space-y-3">
          {resolvedResult?.type === 'repo' && resolvedResult.repository && (
            <div className="p-4 rounded-2xl bg-[#232222] border border-[#333131] flex items-center justify-between gap-4">
              <div className="min-w-0">
                <h4 className="text-sm font-bold text-white truncate m-0">
                  {resolvedResult.repository.full_name}
                </h4>
                {resolvedResult.repository.description && (
                  <p className="text-xs text-[#888] mt-1 m-0 line-clamp-2">
                    {resolvedResult.repository.description}
                  </p>
                )}
                <div className="flex items-center gap-3 text-[11px] text-[#777] mt-2">
                  <span>{resolvedResult.repository.language || 'Unknown'}</span>
                  <span>⭐ {resolvedResult.repository.stargazers_count}</span>
                </div>
              </div>

              <button
                type="button"
                disabled={addingName === resolvedResult.repository.full_name}
                onClick={() => handleAdd(resolvedResult.repository)}
                className="px-4 py-2 rounded-xl bg-[#FF8900] hover:bg-[#e07900] text-xs font-semibold text-white flex items-center gap-1.5 cursor-pointer border-none flex-shrink-0"
              >
                {addingName === resolvedResult.repository.full_name ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Plus className="w-3.5 h-3.5" />
                )}
                Add to Portfolio
              </button>
            </div>
          )}

          {resolvedResult?.type === 'user' && resolvedResult.repositories && (
            <div className="space-y-2.5">
              <span className="text-xs text-[#888] block">
                Found {resolvedResult.repositories.length} public repositories for user{' '}
                <strong className="text-white">@{resolvedResult.username}</strong>:
              </span>

              {resolvedResult.repositories.map((repo) => (
                <div
                  key={repo.full_name}
                  className="p-3.5 rounded-2xl bg-[#232222] border border-[#333131] flex items-center justify-between gap-3"
                >
                  <div className="min-w-0 flex-1">
                    <h5 className="text-xs font-bold text-white truncate m-0">{repo.name}</h5>
                    {repo.description && (
                      <p className="text-[11px] text-[#888] mt-0.5 m-0 line-clamp-1">
                        {repo.description}
                      </p>
                    )}
                    <span className="text-[10px] text-[#777] mt-1 block">
                      {repo.language || 'Unknown'} • ⭐ {repo.stargazers_count}
                    </span>
                  </div>

                  {repo._added ? (
                    <span className="px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-400 text-xs font-medium flex items-center gap-1 border border-emerald-500/20">
                      <Check className="w-3.5 h-3.5" /> Added
                    </span>
                  ) : (
                    <button
                      type="button"
                      disabled={addingName === repo.full_name}
                      onClick={() => handleAdd(repo)}
                      className="px-3 py-1.5 rounded-xl bg-[#2e2d2d] hover:bg-[#FF8900] text-xs font-semibold text-white flex items-center gap-1 cursor-pointer border border-[#3a3838] transition-all flex-shrink-0"
                    >
                      {addingName === repo.full_name ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Plus className="w-3 h-3" />
                      )}
                      Import
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
