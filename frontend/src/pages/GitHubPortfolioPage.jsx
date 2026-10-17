import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import {
  listUserRepositories,
  resolveGitHub,
  addRepositoryToPortfolio,
  analyzeRepository,
  getRepositoryAnalysis,
  deleteUserRepository,
  getPortfolioSummary,
} from '../services/api'
import RepositoryList from '../components/RepositoryList'
import EvidenceExplorer from '../components/EvidenceExplorer'
import ProjectInsightsView from '../components/ProjectInsightsView'
import AddRepositoryModal from '../components/AddRepositoryModal'
import {
  GitBranch,
  Sparkles,
  Plus,
  Play,
  Layers,
  Code2,
  AlertCircle,
  Loader2,
  ExternalLink,
} from 'lucide-react'

export default function GitHubPortfolioPage() {
  const { session } = useAuth()
  const token = session?.access_token

  const [repositories, setRepositories] = useState([])
  const [selectedRepoId, setSelectedRepoId] = useState(null)
  const [currentAnalysis, setCurrentAnalysis] = useState(null)
  const [summaryMetrics, setSummaryMetrics] = useState(null)
  const [activeTab, setActiveTab] = useState('evidence') // 'evidence' | 'insights' | 'overview'

  const [isLoading, setIsLoading] = useState(true)
  const [isResolving, setIsResolving] = useState(false)
  const [isAnalyzingId, setIsAnalyzingId] = useState(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    if (token) {
      loadPortfolioData()
    }
  }, [token])

  async function loadPortfolioData() {
    try {
      setIsLoading(true)
      const [repos, metrics] = await Promise.all([
        listUserRepositories(token),
        getPortfolioSummary(token),
      ])
      setRepositories(repos || [])
      setSummaryMetrics(metrics)

      // Auto-select first repo if none selected
      if (repos && repos.length > 0 && !selectedRepoId) {
        handleSelectRepo(repos[0].id)
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load portfolio.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleSelectRepo(repoId) {
    setSelectedRepoId(repoId)
    setErrorMsg('')
    try {
      const analysis = await getRepositoryAnalysis(repoId, token)
      setCurrentAnalysis(analysis)
    } catch (err) {
      console.error(err)
      setCurrentAnalysis(null)
    }
  }

  async function handleResolveQuery(query) {
    setIsResolving(true)
    try {
      return await resolveGitHub(query, token)
    } finally {
      setIsResolving(false)
    }
  }

  async function handleAddRepo(repoData) {
    const created = await addRepositoryToPortfolio(repoData, token)
    await loadPortfolioData()
    handleSelectRepo(created.id)
  }

  async function handleAnalyze(repoId) {
    setIsAnalyzingId(repoId)
    setErrorMsg('')
    try {
      const result = await analyzeRepository(repoId, token)
      setCurrentAnalysis(result)
      await loadPortfolioData()
    } catch (err) {
      setErrorMsg(err.message || 'Repository analysis failed.')
    } finally {
      setIsAnalyzingId(null)
    }
  }

  async function handleDeleteRepo(repoId) {
    try {
      await deleteUserRepository(repoId, token)
      setRepositories((prev) => prev.filter((r) => r.id !== repoId))
      if (selectedRepoId === repoId) {
        setSelectedRepoId(null)
        setCurrentAnalysis(null)
      }
      getPortfolioSummary(token).then(setSummaryMetrics)
    } catch (err) {
      setErrorMsg(err.message || 'Failed to delete repository.')
    }
  }

  const selectedRepo = repositories.find((r) => r.id === selectedRepoId)

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-[#353333]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-3 m-0">
            <span className="p-2 rounded-xl bg-gradient-to-br from-[#FF8900] to-[#b35f00] text-white">
              <GitBranch className="w-5 h-5" />
            </span>
            GitHub Portfolio Analyzer
          </h1>
          <p className="text-sm text-[#b0abab] mt-1 m-0">
            Extract trustworthy technical skill evidence, verified code snippets, and architecture insights from real code.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="self-start sm:self-auto px-4 py-2.5 rounded-xl bg-[#FF8900] hover:bg-[#e07900] text-sm font-semibold text-white transition-all flex items-center gap-2 cursor-pointer border-none shadow-md"
        >
          <Plus className="w-4 h-4" />
          Add Repository
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-4.5">
          <span className="text-xs text-[#888] font-medium">Connected Repositories</span>
          <p className="text-2xl font-extrabold text-white m-0 mt-1">
            {summaryMetrics?.total_repositories ?? repositories.length}
          </p>
        </div>
        <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-4.5">
          <span className="text-xs text-[#888] font-medium">Analyzed Projects</span>
          <p className="text-2xl font-extrabold text-emerald-400 m-0 mt-1">
            {summaryMetrics?.analyzed_repositories ?? 0}
          </p>
        </div>
        <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-4.5">
          <span className="text-xs text-[#888] font-medium">Distinct Skills Detected</span>
          <p className="text-2xl font-extrabold text-[#FF8900] m-0 mt-1">
            {summaryMetrics?.total_skills_detected ?? 0}
          </p>
        </div>
        <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-4.5">
          <span className="text-xs text-[#888] font-medium">Last Analysis</span>
          <p className="text-xs font-semibold text-[#bbb] m-0 mt-2 truncate">
            {summaryMetrics?.latest_analyzed_at
              ? new Date(summaryMetrics.latest_analyzed_at).toLocaleDateString()
              : 'None yet'}
          </p>
        </div>
      </div>

      {/* Error Banner */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold m-0">Portfolio Error</p>
            <p className="text-xs text-rose-200 m-0 mt-0.5">{errorMsg}</p>
            {errorMsg.toLowerCase().includes('rate limit') && (
              <div className="mt-2 text-xs text-[#ffb054] bg-[#2a1708] border border-[#ff8900]/30 rounded-lg p-2.5">
                <strong>Quick Fix:</strong> GitHub limits unauthenticated requests to 60/hour. Add your GitHub Personal Access Token to <code className="bg-black/40 px-1.5 py-0.5 rounded text-amber-300 font-mono">backend/.env</code>:
                <div className="mt-1 font-mono text-emerald-400">GITHUB_TOKEN=ghp_yourPersonalAccessTokenHere</div>
                The backend will detect it immediately without requiring a restart, granting 5,000 requests/hour.
              </div>
            )}
          </div>
          <button
            onClick={() => setErrorMsg('')}
            className="text-rose-400 hover:text-white bg-transparent border-none cursor-pointer p-1 text-sm font-bold"
            title="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Grid: Left = Repositories list, Right = Repository Detail & Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Repository selector (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 m-0">
              <Layers className="w-4 h-4 text-[#FF8900]" />
              Portfolio Repositories
            </h3>
            <span className="text-xs text-[#888]">{repositories.length} total</span>
          </div>

          {isLoading ? (
            <div className="p-8 text-center bg-[#1a1919] border border-[#353333] rounded-2xl">
              <Loader2 className="w-6 h-6 animate-spin text-[#FF8900] mx-auto mb-2" />
              <p className="text-xs text-[#888] m-0">Loading portfolio...</p>
            </div>
          ) : (
            <RepositoryList
              repositories={repositories}
              selectedRepoId={selectedRepoId}
              onSelectRepo={handleSelectRepo}
              onAnalyzeRepo={handleAnalyze}
              onDeleteRepo={handleDeleteRepo}
              isAnalyzingId={isAnalyzingId}
            />
          )}
        </div>

        {/* Right Column: Active Repository Inspection (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {selectedRepo ? (
            <div className="space-y-6">
              {/* Selected Repo Header Banner */}
              <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-6 shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-[#FF8900]/15 text-[#FF8900] border border-[#FF8900]/30 flex items-center gap-1.5">
                        <GitBranch className="w-3.5 h-3.5" />
                        {selectedRepo.full_name}
                      </span>
                      {selectedRepo.language && (
                        <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#2a2929] text-[#d4cfcf] border border-[#3a3838]">
                          {selectedRepo.language}
                        </span>
                      )}
                      {currentAnalysis?.commit_sha && (
                        <span className="px-2.5 py-1 rounded-md text-xs font-mono text-[#888] bg-[#232222] border border-[#333131]">
                          SHA: {currentAnalysis.commit_sha.slice(0, 7)}
                        </span>
                      )}
                    </div>

                    <h2 className="text-xl font-bold text-white m-0">{selectedRepo.name}</h2>
                    {selectedRepo.description && (
                      <p className="text-xs text-[#b0abab] leading-relaxed m-0">
                        {selectedRepo.description}
                      </p>
                    )}

                    <div className="flex items-center gap-4 text-xs text-[#888] pt-1">
                      <a
                        href={selectedRepo.html_url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="inline-flex items-center gap-1 text-[#FF8900] hover:underline"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Open GitHub Repository
                      </a>
                    </div>
                  </div>

                  <button
                    disabled={isAnalyzingId === selectedRepo.id}
                    onClick={() => handleAnalyze(selectedRepo.id)}
                    className="px-4 py-2.5 rounded-xl bg-[#FF8900] hover:bg-[#e07900] disabled:opacity-50 text-xs font-semibold text-white flex items-center gap-2 cursor-pointer border-none shadow-md transition-all self-start flex-shrink-0"
                  >
                    {isAnalyzingId === selectedRepo.id ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Analyzing Source...
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 fill-current" />
                        {currentAnalysis ? 'Re-run Analysis' : 'Run Full Analysis'}
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* View Tabs */}
              {currentAnalysis ? (
                <div className="space-y-5">
                  <div className="inline-flex rounded-xl bg-[#1a1919] p-1 border border-[#353333]">
                    <button
                      onClick={() => setActiveTab('evidence')}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer border-none ${
                        activeTab === 'evidence'
                          ? 'bg-[#FF8900] text-white shadow'
                          : 'text-[#b0abab] hover:text-white bg-transparent'
                      }`}
                    >
                      <Code2 className="w-3.5 h-3.5" />
                      Skill Evidence ({currentAnalysis.evidence?.length || 0})
                    </button>
                    <button
                      onClick={() => setActiveTab('insights')}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer border-none ${
                        activeTab === 'insights'
                          ? 'bg-[#FF8900] text-white shadow'
                          : 'text-[#b0abab] hover:text-white bg-transparent'
                      }`}
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      Project Quality & Architecture
                    </button>
                  </div>

                  {activeTab === 'evidence' ? (
                    <EvidenceExplorer
                      evidence={currentAnalysis.evidence || []}
                      repoFullName={selectedRepo.full_name}
                    />
                  ) : (
                    <ProjectInsightsView
                      insights={currentAnalysis.project_insights}
                      commitSha={currentAnalysis.commit_sha}
                    />
                  )}
                </div>
              ) : (
                <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-10 text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-[#2a2929] flex items-center justify-center mx-auto text-[#FF8900]">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <h3 className="text-base font-bold text-white m-0">Ready for Evidence Analysis</h3>
                  <p className="text-xs text-[#888] max-w-sm mx-auto m-0">
                    Click "Run Full Analysis" to inspect the repository tree, discover architecture components, and extract verified code evidence.
                  </p>
                  <button
                    disabled={isAnalyzingId === selectedRepo.id}
                    onClick={() => handleAnalyze(selectedRepo.id)}
                    className="mt-2 px-5 py-2.5 rounded-xl bg-[#FF8900] hover:bg-[#e07900] text-xs font-semibold text-white inline-flex items-center gap-2 cursor-pointer border-none"
                  >
                    {isAnalyzingId === selectedRepo.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Play className="w-3.5 h-3.5 fill-current" />
                    )}
                    Start Analysis
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-12 text-center text-[#888] text-sm">
              Select a repository from your portfolio to inspect its skill evidence and architectural insights.
            </div>
          )}
        </div>
      </div>

      {/* Add Repository Modal */}
      <AddRepositoryModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onResolve={handleResolveQuery}
        onAddRepo={handleAddRepo}
        isResolving={isResolving}
      />
    </div>
  )
}
