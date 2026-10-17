/**
 * DashboardPage — Main authenticated dashboard with welcome, checklist,
 * feature cards, recent assessments, and repository monitoring sections.
 * Uses real user data — no fabricated scores or fake history.
 */
import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { checkBackendHealth, getSystemStatus, API_BASE_URL } from '../services/api'
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  CheckCircle2,
  Circle,
  Clock,
  GitBranch,
  RefreshCw,
  Server,
  Sparkles,
  Target,
  TrendingUp,
  Inbox,
} from 'lucide-react'

export default function DashboardPage() {
  const { user } = useAuth()
  const displayName =
    user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'

  // Backend health status
  const [backendOk, setBackendOk] = useState(null)
  const [latencyMs, setLatencyMs] = useState(null)

  const checkHealth = useCallback(async () => {
    try {
      const data = await checkBackendHealth()
      setBackendOk(true)
      setLatencyMs(data.latencyMs)
    } catch {
      setBackendOk(false)
      setLatencyMs(null)
    }
  }, [])

  useEffect(() => {
    checkHealth()
  }, [checkHealth])

  // Getting started checklist
  const checklist = [
    { label: 'Select a target job posting', done: false },
    { label: 'Add your GitHub username', done: false },
    { label: 'Run your first portfolio assessment', done: false },
  ]

  // Feature quick-access cards
  const featureCards = [
    {
      icon: BookOpen,
      title: 'Job Analysis',
      description: 'Parse a real job posting to extract required skills and competencies.',
      action: 'Active (Phase 5)',
      link: '/dashboard/jobs',
      color: '#FF8900',
    },
    {
      icon: GitBranch,
      title: 'GitHub Portfolio',
      description: 'Connect your GitHub profile to analyze repository evidence.',
      action: 'Active (Phase 6)',
      link: '/dashboard/github',
      color: '#22c55e',
    },
    {
      icon: BarChart3,
      title: 'Skill-Gap Assessment',
      description: 'Compare your demonstrated skills against job requirements.',
      action: 'Active (Phase 7)',
      link: '/dashboard/skills',
      color: '#8b5cf6',
    },
  ]

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* ─── WELCOME SECTION ─── */}
      <div className="rounded-2xl border border-[#3a3838] bg-gradient-to-br from-[#2a2929] via-[#252424] to-[#1e1d1d] p-6 sm:p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#FF8900]/[0.03] rounded-full blur-[80px] -translate-y-1/2 translate-x-1/4 pointer-events-none" />

        <div className="relative">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-[#FF8900]" />
            <span className="text-xs font-semibold uppercase tracking-wider text-[#FF8900]">
              Dashboard
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight mb-2">
            Welcome back, {displayName}
          </h1>

          <p className="text-sm text-[#a8a3a3] leading-relaxed max-w-2xl">
            CareerProof AI compares your GitHub portfolio evidence with real job requirements
            to deliver objective, evidence-based career coaching. Complete the checklist below
            to run your first assessment.
          </p>

          {/* Mini backend status */}
          <div className="mt-4 flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-[#9c9797]" />
              <span className="text-[#9c9797]">Backend:</span>
              {backendOk === null ? (
                <span className="text-amber-400">Checking…</span>
              ) : backendOk ? (
                <span className="text-emerald-400">
                  Connected {latencyMs !== null && `(${latencyMs}ms)`}
                </span>
              ) : (
                <span className="text-rose-400">Offline</span>
              )}
            </div>
            <button
              onClick={checkHealth}
              className="flex items-center gap-1 text-[#9c9797] hover:text-[#FF8900] bg-transparent border-none cursor-pointer transition-colors text-xs"
            >
              <RefreshCw className="w-3 h-3" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* ─── GETTING STARTED CHECKLIST ─── */}
      <div className="rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6">
        <h2 className="text-base font-semibold text-white mb-1">Getting Started</h2>
        <p className="text-xs text-[#9c9797] mb-4">
          Complete these steps to run your first evidence-based assessment.
        </p>

        <div className="space-y-3">
          {checklist.map((item, i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-4 py-3 rounded-xl border border-[#383636] bg-[#1c1b1b]"
            >
              {item.done ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
              ) : (
                <Circle className="w-5 h-5 text-[#6b6666] flex-shrink-0" />
              )}
              <span className={`text-sm ${item.done ? 'text-emerald-300 line-through' : 'text-[#d4cfcf]'}`}>
                {item.label}
              </span>
              {!item.done && (
                <span className="ml-auto text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/25 tracking-wider">
                  Pending
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ─── FEATURE CARDS ─── */}
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#9c9797] mb-4">
          Available Features
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {featureCards.map((card) => {
            const Icon = card.icon
            return (
              <Link
                key={card.title}
                to={card.link}
                className="rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6 group hover:border-[#FF8900]/40 transition-all block cursor-pointer"
              >
                <div className="flex items-start justify-between mb-4">
                  <div
                    className="p-2.5 rounded-xl bg-[#1c1b1b] border border-[#383636] group-hover:border-[#FF8900]/30 transition-colors"
                    style={{ color: card.color }}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-[#333131] text-[#b0abab] border border-[#484545] tracking-wider group-hover:text-white transition-colors">
                    {card.action}
                  </span>
                </div>
                <h3 className="text-base font-semibold text-white mb-2 group-hover:text-[#FF8900] transition-colors">{card.title}</h3>
                <p className="text-sm text-[#a8a3a3] leading-relaxed">{card.description}</p>
              </Link>
            )
          })}
        </div>
      </div>

      {/* ─── RECENT ASSESSMENTS ─── */}
      <div className="rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-white mb-0.5">Recent Assessments</h2>
            <p className="text-xs text-[#9c9797]">Your portfolio assessment history.</p>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-[#9c9797]">
            <Clock className="w-3.5 h-3.5" />
            <span>Updated in real-time</span>
          </div>
        </div>

        {/* Empty state */}
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <div className="w-14 h-14 rounded-2xl bg-[#1c1b1b] border border-[#383636] flex items-center justify-center mb-4">
            <Inbox className="w-7 h-7 text-[#6b6666]" />
          </div>
          <p className="text-sm font-medium text-[#d4cfcf] mb-1">No assessments yet</p>
          <p className="text-xs text-[#9c9797] max-w-xs">
            Complete the Getting Started checklist to run your first evidence-based
            skill-gap assessment.
          </p>
        </div>
      </div>

      {/* ─── REPOSITORY MONITORING ─── */}
      <div className="rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-[#1c1b1b] border border-[#383636] text-[#FF8900] flex-shrink-0">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white mb-1">Repository Monitoring</h2>
            <p className="text-sm text-[#a8a3a3] leading-relaxed">
              Once you complete your first assessment, CareerProof AI will automatically
              re-analyze your repositories when you push code updates. Reassessment will
              reflect genuine improvements in your skill profile — available in a future phase.
            </p>
            <span className="inline-block mt-3 text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-[#333131] text-[#b0abab] border border-[#484545] tracking-wider">
              Coming in Phase 5
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
