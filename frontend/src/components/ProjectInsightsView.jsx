import { useState } from 'react'
import {
  Layers,
  Cpu,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Award,
  TrendingUp,
  FileSearch,
} from 'lucide-react'

export default function ProjectInsightsView({ insights, _commitSha }) {
  const [activeTab, setActiveTab] = useState('architecture') // 'architecture' | 'tech' | 'practices' | 'strengths' | 'improvements' | 'coverage'

  if (!insights) {
    return (
      <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-8 text-center text-sm text-[#888]">
        No project insights available for this repository run.
      </div>
    )
  }

  const {
    tech_stack = [],
    architecture = {},
    engineering_practices = [],
    strengths = [],
    improvements = [],
    coverage = {},
  } = insights

  const tabs = [
    { id: 'architecture', label: 'Architecture Overview', icon: Layers },
    { id: 'tech', label: `Tech Stack (${tech_stack.length})`, icon: Cpu },
    { id: 'practices', label: `Engineering Practices (${engineering_practices.length})`, icon: CheckCircle2 },
    { id: 'strengths', label: `Strengths (${strengths.length})`, icon: Award },
    { id: 'improvements', label: `Improvements (${improvements.length})`, icon: TrendingUp },
    { id: 'coverage', label: 'Coverage & Limitations', icon: FileSearch },
  ]

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none border-b border-[#353333]">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer border-none flex-shrink-0 ${
                isActive
                  ? 'bg-[#FF8900] text-white shadow-md'
                  : 'bg-[#232222] text-[#b0abab] hover:text-white hover:bg-[#2e2d2d]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* Tab: Architecture Overview */}
      {activeTab === 'architecture' && (
        <div className="space-y-4">
          <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2 m-0">
              <Layers className="w-5 h-5 text-[#FF8900]" />
              System Architecture Summary
            </h3>
            <p className="text-sm text-[#d4cfcf] leading-relaxed m-0">
              {architecture.summary || 'Architecture derived from directory structure, module imports, and route definitions.'}
            </p>

            {architecture.basis_explanation && (
              <p className="text-xs text-[#888] italic m-0 pt-1">
                Basis of inference: {architecture.basis_explanation}
              </p>
            )}
          </div>

          {/* Architecture Components */}
          {architecture.components && architecture.components.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {architecture.components.map((comp, i) => (
                <div key={i} className="bg-[#1a1919] border border-[#353333] rounded-2xl p-4 space-y-1.5">
                  <span className="text-xs font-mono font-semibold text-[#FF8900] bg-[#FF8900]/10 px-2 py-0.5 rounded border border-[#FF8900]/20">
                    {comp.component || `Component ${i+1}`}
                  </span>
                  <p className="text-xs text-white font-medium m-0 pt-1">{comp.description}</p>
                  {comp.basis && (
                    <p className="text-[11px] text-[#888] m-0">Observed evidence: {comp.basis}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Mermaid / Text Diagram */}
          {architecture.diagram_mermaid && (
            <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-5 space-y-2">
              <h4 className="text-xs font-semibold text-[#b0abab] uppercase tracking-wider m-0">
                Architecture Flow Diagram
              </h4>
              <pre className="bg-[#121212] border border-[#2e2d2d] rounded-xl p-4 text-xs text-[#FF8900] font-mono whitespace-pre overflow-x-auto m-0">
                {architecture.diagram_mermaid}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Tab: Tech Stack */}
      {activeTab === 'tech' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {tech_stack.map((item, i) => (
            <div key={i} className="bg-[#1a1919] border border-[#353333] rounded-2xl p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <h4 className="text-sm font-bold text-white m-0">{item.name}</h4>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[#2a2929] text-[#9c9797] border border-[#3a3838]">
                    {item.category}
                  </span>
                </div>
                <p className="text-xs text-[#b0abab] m-0">
                  Detected in: <span className="font-mono text-[#d4cfcf]">{item.detection_source}</span>
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-[#2a2929] flex items-center justify-between text-[11px]">
                <span className="text-[#888]">Evidence: {item.evidence_type}</span>
                <span className={item.is_direct_implementation ? 'text-emerald-400 font-medium' : 'text-amber-400 font-medium'}>
                  {item.is_direct_implementation ? 'Direct implementation' : 'Mention / Dependency'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Engineering Practices */}
      {activeTab === 'practices' && (
        <div className="space-y-3">
          {engineering_practices.map((ep, i) => {
            const isPresent = ep.status === 'present'
            const isIncomplete = ep.status === 'incomplete'
            const badgeCls = isPresent
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25'
              : isIncomplete
              ? 'bg-amber-500/10 text-amber-400 border-amber-500/25'
              : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/25'
            const Icon = isPresent ? CheckCircle2 : isIncomplete ? AlertCircle : HelpCircle

            return (
              <div key={i} className="bg-[#1a1919] border border-[#353333] rounded-2xl p-4.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-xl bg-[#232222] border border-[#353333] mt-0.5">
                    <Icon className={`w-4 h-4 ${isPresent ? 'text-emerald-400' : isIncomplete ? 'text-amber-400' : 'text-zinc-400'}`} />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white m-0">{ep.practice}</h4>
                    <p className="text-xs text-[#c9c5c5] mt-1 m-0 leading-relaxed">{ep.evidence}</p>
                    {ep.recommendation && (
                      <p className="text-[11px] text-[#FF8900] mt-1 m-0">Tip: {ep.recommendation}</p>
                    )}
                  </div>
                </div>

                <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold border self-start sm:self-center flex-shrink-0 uppercase tracking-wider text-[10px] ${badgeCls}`}>
                  {ep.status}
                </span>
              </div>
            )
          })}
        </div>
      )}

      {/* Tab: Strengths */}
      {activeTab === 'strengths' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {strengths.map((str, i) => (
            <div key={i} className="bg-[#1a1919] border border-[#353333] rounded-2xl p-5 space-y-2">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-[#FF8900]" />
                <h4 className="text-sm font-bold text-white m-0">{str.title}</h4>
              </div>
              <p className="text-xs text-[#d4cfcf] leading-relaxed m-0">{str.explanation}</p>
              {str.evidence_source && (
                <p className="text-[11px] text-[#888] font-mono m-0 pt-1">
                  Observed in: {str.evidence_source}
                </p>
              )}
              {str.why_useful && (
                <div className="p-2.5 rounded-xl bg-[#232222] text-[11px] text-[#b0abab] border border-[#333131]">
                  <strong className="text-white">Why it matters: </strong>
                  {str.why_useful}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tab: Improvements */}
      {activeTab === 'improvements' && (
        <div className="space-y-3.5">
          {improvements.map((imp, i) => {
            const prio = imp.priority || 'medium'
            const badgeCls =
              prio === 'high'
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/25'
                : prio === 'medium'
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/25'
                : 'bg-sky-500/10 text-sky-400 border-sky-500/25'

            return (
              <div key={i} className="bg-[#1a1919] border border-[#353333] rounded-2xl p-5 space-y-2.5">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[#FF8900]" />
                    <h4 className="text-sm font-bold text-white m-0">{imp.title}</h4>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${badgeCls}`}>
                    {prio} priority
                  </span>
                </div>

                <p className="text-xs text-[#d4cfcf] leading-relaxed m-0">{imp.issue_explanation}</p>

                <div className="p-3 rounded-xl bg-[#232222] border border-[#333131] text-xs text-[#b0abab]">
                  <strong className="text-emerald-400">Actionable Suggestion: </strong>
                  {imp.suggested_improvement}
                </div>

                {imp.evidence_source && (
                  <p className="text-[11px] text-[#888] font-mono m-0">Reference: {imp.evidence_source}</p>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Tab: Coverage & Limitations */}
      {activeTab === 'coverage' && (
        <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-6 space-y-5">
          <h3 className="text-base font-bold text-white flex items-center gap-2 m-0">
            <FileSearch className="w-5 h-5 text-[#FF8900]" />
            Analysis Coverage & Technical Transparency
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 rounded-xl bg-[#232222] border border-[#333131]">
              <span className="text-xs text-[#888]">Discovered Files</span>
              <p className="text-xl font-bold text-white m-0 mt-1">{coverage.total_files_discovered ?? 0}</p>
            </div>
            <div className="p-3 rounded-xl bg-[#232222] border border-[#333131]">
              <span className="text-xs text-[#888]">Analyzed Files</span>
              <p className="text-xl font-bold text-emerald-400 m-0 mt-1">{coverage.files_analyzed_count ?? 0}</p>
            </div>
            <div className="p-3 rounded-xl bg-[#232222] border border-[#333131]">
              <span className="text-xs text-[#888]">Skipped Files</span>
              <p className="text-xl font-bold text-amber-400 m-0 mt-1">{coverage.files_skipped_count ?? 0}</p>
            </div>
            <div className="p-3 rounded-xl bg-[#232222] border border-[#333131]">
              <span className="text-xs text-[#888]">Analysis Method</span>
              <p className="text-xs font-semibold text-[#FF8900] m-0 mt-2">Static Inspection</p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-200/90 leading-relaxed space-y-1">
            <strong className="text-amber-300 font-semibold block">Declared Limitations:</strong>
            <p className="m-0">{coverage.limitations || 'Static code inspection only. Runtime behavior, tests execution, and dynamic network queries are evaluated analytically.'}</p>
          </div>

          {coverage.skipped_reasons && coverage.skipped_reasons.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-[#888] uppercase tracking-wider m-0">
                Sample Skipped Files (Bounded Safety / Binary / Size Exclusions)
              </h4>
              <ul className="text-xs text-[#888] space-y-1 list-disc pl-4 font-mono">
                {coverage.skipped_reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
