import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Activity,
  GitBranch,
  GitCommit,
  RefreshCw,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  ExternalLink,
  Layers,
  FileCode,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  Zap
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import {
  getMonitoringStatus,
  syncRepository,
  listChangeEvents,
  retryChangeEvent
} from '../services/api'
import ChangeEventDetailModal from '../components/ChangeEventDetailModal'

export default function RepositoryActivityPage() {
  const { session } = useAuth()
  const token = session?.access_token
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [syncingRepoId, setSyncingRepoId] = useState(null)
  const [syncMessage, setSyncMessage] = useState(null)
  const [error, setError] = useState(null)

  const [monitoringStatus, setMonitoringStatus] = useState(null)
  const [events, setEvents] = useState([])
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')

  const fetchData = useCallback(async (isSilent = false) => {
    if (!token) return
    if (!isSilent) setLoading(true)
    else setRefreshing(true)
    setError(null)

    try {
      const [statusRes, eventsRes] = await Promise.all([
        getMonitoringStatus(token),
        listChangeEvents(token, 30)
      ])
      setMonitoringStatus(statusRes)
      setEvents(eventsRes.events || [])
    } catch (err) {
      setError(err.message || 'Failed to load repository monitoring activity.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [token])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  async function handleSyncRepository(repoId) {
    if (!token || syncingRepoId) return
    setSyncingRepoId(repoId)
    setSyncMessage(null)
    try {
      const result = await syncRepository(repoId, token)
      setSyncMessage({
        type: result.has_changes ? 'success' : 'info',
        text: result.message
      })
      // Refresh event list and repository status
      await fetchData(true)
    } catch (err) {
      setSyncMessage({
        type: 'error',
        text: err.message || 'Synchronization check failed.'
      })
    } finally {
      setSyncingRepoId(null)
    }
  }

  async function handleRetryEvent(eventId) {
    if (!token) return
    try {
      const updated = await retryChangeEvent(eventId, token)
      setSelectedEvent(updated)
      await fetchData(true)
    } catch (err) {
      alert(`Retry failed: ${err.message}`)
    }
  }

  function handleOpenAssessment(assessmentId) {
    navigate('/dashboard/skills', { state: { selectedAssessmentId: assessmentId } })
  }

  const filteredEvents = events.filter((ev) => {
    if (statusFilter === 'all') return true
    return ev.status === statusFilter
  })

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* ─── PAGE HEADER ─── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#353333] pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#FF8900]/10 border border-[#FF8900]/30 flex items-center justify-center text-[#FF8900]">
              <Activity className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Repository Activity &amp; Reassessment</h1>
          </div>
          <p className="text-sm text-[#b0abab] mt-1">
            Automatic GitHub change detection, real-time evidence reconciliation, and career reassessment.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing || loading}
            className="px-3.5 py-2 rounded-xl bg-[#282626] hover:bg-[#333131] border border-[#3d3b3b] text-sm font-medium text-white transition-all flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh Status'}</span>
          </button>
        </div>
      </div>

      {/* ─── SYNC FEEDBACK BANNER ─── */}
      {syncMessage && (
        <div className={`p-4 rounded-xl border flex items-center justify-between gap-3 text-sm animate-fadeIn ${
          syncMessage.type === 'success'
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            : syncMessage.type === 'error'
            ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
            : 'bg-blue-500/10 border-blue-500/30 text-blue-300'
        }`}>
          <div className="flex items-center gap-2.5">
            {syncMessage.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />}
            {syncMessage.type === 'error' && <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />}
            {syncMessage.type === 'info' && <Clock className="w-5 h-5 text-blue-400 flex-shrink-0" />}
            <span>{syncMessage.text}</span>
          </div>
          <button
            onClick={() => setSyncMessage(null)}
            className="text-xs opacity-70 hover:opacity-100 underline ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ─── ERROR STATE ─── */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ─── SECTION 1: MONITORING OVERVIEW & REPOSITORIES ─── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-[#FF8900]" />
            <h2 className="text-base font-semibold text-white">Monitored Repositories &amp; Polling Status</h2>
          </div>
          {monitoringStatus && (
            <div className="flex items-center gap-2 text-xs">
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Worker: {monitoringStatus.active_worker_status === 'active' ? 'Continuous Polling' : 'Idle'}
              </span>
              <span className="text-[#8e8a8a] hidden sm:inline">
                Interval: {monitoringStatus.poll_interval_seconds}s
              </span>
            </div>
          )}
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-[#8e8a8a] bg-[#1a1919] border border-[#353333] rounded-2xl">
            <div className="w-6 h-6 border-2 border-[#FF8900] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            Loading repository monitoring status...
          </div>
        ) : (!monitoringStatus?.repositories || monitoringStatus.repositories.length === 0) ? (
          <div className="p-8 text-center bg-[#1a1919] border border-[#353333] rounded-2xl space-y-3">
            <GitBranch className="w-10 h-10 text-[#8e8a8a] mx-auto opacity-50" />
            <h3 className="text-base font-semibold text-white">No Connected Repositories Yet</h3>
            <p className="text-xs text-[#a09e9e] max-w-md mx-auto">
              Connect your GitHub repositories in the GitHub Portfolio section to enable automatic change detection and career reassessment.
            </p>
            <button
              onClick={() => navigate('/dashboard/github')}
              className="mt-2 px-4 py-2 bg-[#FF8900] hover:bg-[#e07800] text-black font-semibold text-xs rounded-xl transition-colors"
            >
              Go to GitHub Portfolio
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {monitoringStatus.repositories.map((repo) => {
              const isSyncing = syncingRepoId === repo.id
              const analyzedSha = repo.last_analyzed_commit_sha ? repo.last_analyzed_commit_sha.substring(0, 7) : 'None'
              const latestSha = repo.latest_commit_sha ? repo.latest_commit_sha.substring(0, 7) : null

              return (
                <div
                  key={repo.id}
                  className="bg-[#1a1919] border border-[#353333] rounded-2xl p-4 flex flex-col justify-between hover:border-[#4d4a4a] transition-all group"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <h4 className="text-sm font-bold text-white truncate group-hover:text-[#FF8900] transition-colors">
                          {repo.name}
                        </h4>
                        <p className="text-xs text-[#8e8a8a] truncate">{repo.full_name}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#282626] text-amber-300 border border-[#3d3b3b]">
                        {repo.default_branch}
                      </span>
                    </div>

                    <div className="space-y-1.5 text-xs font-mono bg-[#232222] p-2.5 rounded-xl border border-[#2d2b2b]">
                      <div className="flex items-center justify-between text-[#8e8a8a]">
                        <span>Analyzed Commit:</span>
                        <span className="text-zinc-200">{analyzedSha}</span>
                      </div>
                      {latestSha && latestSha !== analyzedSha && (
                        <div className="flex items-center justify-between text-amber-400">
                          <span>Detected Head:</span>
                          <span className="font-semibold">{latestSha} (new!)</span>
                        </div>
                      )}
                      <div className="flex items-center justify-between text-[#8e8a8a] pt-1 border-t border-[#2d2b2b]">
                        <span>Last Check:</span>
                        <span className="text-[#a09e9e]">
                          {repo.last_polled_at ? new Date(repo.last_polled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Pending'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-[#2d2b2b] flex items-center justify-between">
                    <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-medium">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      Monitoring active
                    </span>

                    <button
                      onClick={() => handleSyncRepository(repo.id)}
                      disabled={isSyncing}
                      className="px-3 py-1.5 bg-[#2d2b2b] hover:bg-[#383636] text-white rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 disabled:opacity-50"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                      <span>{isSyncing ? 'Checking...' : 'Check Changes'}</span>
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* ─── SECTION 2: CHANGE DETECTION & REASSESSMENT EVENTS ─── */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <GitCommit className="w-4 h-4 text-[#FF8900]" />
            <h2 className="text-base font-semibold text-white">
              Detected Change Events &amp; Assessment History ({events.length})
            </h2>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1 bg-[#1a1919] border border-[#353333] p-1 rounded-xl text-xs">
            {['all', 'completed', 'pending', 'failed'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-lg font-medium capitalize transition-colors ${
                  statusFilter === st
                    ? 'bg-[#FF8900] text-black font-semibold'
                    : 'text-[#8e8a8a] hover:text-white hover:bg-[#282626]'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-[#8e8a8a] bg-[#1a1919] border border-[#353333] rounded-2xl">
            <div className="w-6 h-6 border-2 border-[#FF8900] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            Loading change history...
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="p-12 text-center bg-[#1a1919] border border-[#353333] rounded-2xl space-y-3">
            <Clock className="w-10 h-10 text-[#8e8a8a] mx-auto opacity-40" />
            <h3 className="text-base font-semibold text-white">No Change Events Recorded Yet</h3>
            <p className="text-xs text-[#a09e9e] max-w-lg mx-auto">
              When commits are pushed to your GitHub repositories, CareerProof AI automatically detects the change,
              inspects updated source files, reconciles your verified skills, and reassesses any saved job matches.
            </p>
          </div>
        ) : (
          <div className="border border-[#353333] rounded-2xl overflow-hidden bg-[#1a1919] divide-y divide-[#2d2b2b]">
            {filteredEvents.map((ev) => {
              const shortSha = ev.detected_commit_sha ? ev.detected_commit_sha.substring(0, 7) : 'Commit'
              const summary = ev.evidence_change_summary || {}
              const updates = ev.assessment_updates || []

              const statusBadgeStyles = {
                completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
                processing: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
                pending: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
                failed: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
                skipped: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30',
              }

              return (
                <div
                  key={ev.id}
                  className="p-5 hover:bg-[#212020] transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-2 min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-white">{ev.repository_name}</span>
                      <code className="text-xs font-mono px-2 py-0.5 rounded bg-[#282626] text-amber-300 border border-[#3d3b3b]">
                        {shortSha}
                      </code>
                      <span className={`px-2 py-0.5 text-[11px] font-medium rounded-full border ${statusBadgeStyles[ev.status] || statusBadgeStyles.pending}`}>
                        {ev.status}
                      </span>
                    </div>

                    {ev.commit_message && (
                      <p className="text-xs text-zinc-300 font-mono line-clamp-1">
                        {ev.commit_message}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-[#8e8a8a]">
                      <span>{new Date(ev.detected_at).toLocaleString()}</span>
                      <span>&bull;</span>
                      <span>{ev.changed_files_count || 0} changed files</span>

                      {summary.skills_affected && summary.skills_affected.length > 0 && (
                        <>
                          <span>&bull;</span>
                          <span className="text-amber-200">
                            {summary.skills_affected.length} skills affected ({summary.skills_affected.slice(0, 3).join(', ')})
                          </span>
                        </>
                      )}
                    </div>

                    {/* Assessment updates summary banner */}
                    {updates.length > 0 && (
                      <div className="pt-1 flex flex-wrap items-center gap-2">
                        {updates.map((u, i) => {
                          const delta = u.score_delta || 0
                          const isPos = delta > 0
                          const isNeg = delta < 0
                          return (
                            <span
                              key={i}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#282626] border border-[#3d3b3b] text-xs text-zinc-200"
                            >
                              <span className="font-medium text-white">{u.job_title}:</span>
                              <span>{u.previous_score ?? 'N/A'}% &rarr; {u.new_score ?? 'N/A'}%</span>
                              <span className={`font-bold ${isPos ? 'text-emerald-400' : isNeg ? 'text-rose-400' : 'text-zinc-400'}`}>
                                ({delta > 0 ? `+${delta}%` : `${delta}%`})
                              </span>
                            </span>
                          )
                        })}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => setSelectedEvent(ev)}
                      className="px-3.5 py-2 bg-[#2d2b2b] hover:bg-[#383636] text-white rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5"
                    >
                      <span>View Details</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>

                    {ev.status === 'failed' && (
                      <button
                        onClick={() => handleRetryEvent(ev.id)}
                        className="px-3.5 py-2 bg-rose-600/80 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold transition-colors"
                      >
                        Retry
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* ─── CHANGE EVENT DETAIL MODAL ─── */}
      {selectedEvent && (
        <ChangeEventDetailModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
          onRetry={handleRetryEvent}
          onOpenAssessment={handleOpenAssessment}
        />
      )}
    </div>
  )
}
