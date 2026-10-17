import { useState } from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Briefcase,
  GitBranch,
  Calendar,
  ChevronDown,
  ChevronUp,
  ShieldAlert
} from 'lucide-react'

export default function AssessmentScoreOverview({ assessment }) {
  const [showMethodology, setShowMethodology] = useState(false)

  if (!assessment) return null

  const score = assessment.match_score
  const total = assessment.total_requirements || 0
  const demonstrated = assessment.demonstrated_count || 0
  const partial = assessment.partially_demonstrated_count || 0
  const notDemonstrated = assessment.not_demonstrated_count || 0

  const repos = assessment.repositories_snapshot || []

  // Color gradient based on score
  let scoreColorClass = 'text-emerald-400'
  let scoreBgClass = 'from-emerald-500/10 to-emerald-500/5 border-emerald-500/30'
  if (score === null || score === undefined) {
    scoreColorClass = 'text-zinc-400'
    scoreBgClass = 'from-zinc-500/10 to-zinc-500/5 border-zinc-500/30'
  } else if (score < 50) {
    scoreColorClass = 'text-amber-400'
    scoreBgClass = 'from-amber-500/10 to-amber-500/5 border-amber-500/30'
  } else if (score < 75) {
    scoreColorClass = 'text-[#FF8900]'
    scoreBgClass = 'from-[#FF8900]/10 to-[#FF8900]/5 border-[#FF8900]/30'
  }

  const formattedDate = assessment.completed_at || assessment.created_at
    ? new Date(assessment.completed_at || assessment.created_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'Recent'

  return (
    <div className="space-y-4">
      {/* Primary Overview Banner */}
      <div className={`p-6 rounded-2xl bg-gradient-to-br ${scoreBgClass} border relative overflow-hidden backdrop-blur-sm`}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Left: Job Info & Repo Tags */}
          <div className="space-y-3 flex-1">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="px-2.5 py-1 rounded-full bg-[#353333] text-[#b0abab] font-mono flex items-center gap-1.5 border border-[#444]">
                <Calendar className="w-3 h-3 text-[#FF8900]" />
                {formattedDate}
              </span>
              <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20">
                Phase 7 Verified
              </span>
            </div>

            <div>
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-[#FF8900]" />
                {assessment.job_title || 'Target Job Role'}
              </h2>
              <p className="text-sm text-[#b0abab] mt-0.5">
                {assessment.company_name || 'Target Employer'} &bull; Evaluated against {repos.length} selected {repos.length === 1 ? 'repository' : 'repositories'}
              </p>
            </div>

            {/* Repositories badges */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs text-[#8c8888] flex items-center gap-1">
                <GitBranch className="w-3.5 h-3.5 text-[#FF8900]" /> Analyzed Repositories:
              </span>
              {repos.map((r, idx) => (
                <span
                  key={r.id || idx}
                  className="px-2.5 py-0.5 rounded-md bg-[#2a2828] text-xs font-mono text-[#dcd7d7] border border-[#3f3d3d]"
                  title={`Analyzed commit: ${r.last_analyzed_commit_sha ? r.last_analyzed_commit_sha.substring(0, 7) : 'latest'}`}
                >
                  {r.name || r.full_name}
                  {r.language && <span className="ml-1 text-[10px] text-[#FF8900]">({r.language})</span>}
                </span>
              ))}
            </div>
          </div>

          {/* Right: Score Card */}
          <div className="flex items-center gap-6 bg-[#1a1919]/80 p-5 rounded-xl border border-[#353333] shrink-0">
            <div className="text-center">
              <div className="text-[11px] font-semibold text-[#8c8888] tracking-wider uppercase">
                Portfolio Match Score
              </div>
              <div className={`text-4xl font-extrabold tracking-tight mt-1 ${scoreColorClass}`}>
                {score !== null && score !== undefined ? `${score}%` : 'N/A'}
              </div>
              <div className="text-[10px] text-[#8c8888] mt-1 max-w-[140px] leading-tight">
                Deterministic weighted evidence match
              </div>
            </div>

            <div className="w-px h-16 bg-[#353333] hidden sm:block" />

            {/* Status Breakdown Counts */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3 text-center sm:text-left">
              <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                <div className="flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Demonstrated
                </div>
                <div className="text-lg font-bold text-white mt-0.5">{demonstrated}</div>
              </div>

              <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-center gap-1 text-[11px] font-medium text-amber-400">
                  <AlertTriangle className="w-3.5 h-3.5" /> Partial
                </div>
                <div className="text-lg font-bold text-white mt-0.5">{partial}</div>
              </div>

              <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20">
                <div className="flex items-center gap-1 text-[11px] font-medium text-rose-400">
                  <XCircle className="w-3.5 h-3.5" /> Not Found
                </div>
                <div className="text-lg font-bold text-white mt-0.5">{notDemonstrated}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Methodology Accordion Trigger */}
        <div className="mt-4 pt-3 border-t border-[#353333]/60 flex items-center justify-between text-xs text-[#b0abab]">
          <div className="flex items-center gap-1.5 text-zinc-400">
            <ShieldAlert className="w-4 h-4 text-[#FF8900]" />
            <span>Labels reflect verified code in analyzed repositories, not personal ability.</span>
          </div>

          <button
            onClick={() => setShowMethodology(!showMethodology)}
            className="flex items-center gap-1 text-[#FF8900] hover:text-[#ffa333] font-medium transition-colors"
          >
            <span>{showMethodology ? 'Hide Scoring Method' : 'View Scoring Methodology'}</span>
            {showMethodology ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Collapsible Methodology Card */}
        {showMethodology && (
          <div className="mt-4 p-4 rounded-xl bg-[#1a1919] border border-[#353333] text-xs text-[#b0abab] space-y-2 animate-fadeIn">
            <h4 className="font-semibold text-white flex items-center gap-1.5">
              <HelpCircle className="w-4 h-4 text-[#FF8900]" />
              Deterministic Scoring Formula & Parameters
            </h4>
            <p>
              The portfolio match score is calculated deterministically with zero artificial hallucination:
            </p>
            <div className="p-2.5 rounded-lg bg-[#232222] font-mono text-[11px] text-[#FF8900] border border-[#353333]">
              Match Score = 100 &times; &Sigma;(Requirement Weight &times; Status Score) / &Sigma;(Requirement Weight)
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-[11px]">
              <div>
                <span className="font-semibold text-white">Status Scores:</span>
                <ul className="list-disc list-inside mt-1 space-y-0.5 text-[#b0abab]">
                  <li><strong className="text-emerald-400">Demonstrated:</strong> 1.0 (direct code/tests verified)</li>
                  <li><strong className="text-amber-400">Partially demonstrated:</strong> 0.5 (dependency or configuration only)</li>
                  <li><strong className="text-rose-400">Not demonstrated:</strong> 0.0 (no evidence in analyzed files)</li>
                </ul>
              </div>
              <div>
                <span className="font-semibold text-white">Requirement Importance Weights:</span>
                <ul className="list-disc list-inside mt-1 space-y-0.5 text-[#b0abab]">
                  <li><strong className="text-white">Required:</strong> 1.0 (vital core requirement)</li>
                  <li><strong className="text-white">Preferred:</strong> 0.5 (nice-to-have skill)</li>
                </ul>
              </div>
            </div>
            <p className="text-[11px] text-zinc-400 pt-1 italic">
              Limitation: The assessment strictly represents evidence extracted from repository files and commits processed during Phase 6 analysis. Absence of evidence does not indicate absence of skill.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
