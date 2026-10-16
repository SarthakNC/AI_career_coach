import { Code2, FileSearch, Sparkles, Target } from 'lucide-react'

export default function ProjectDescriptionCard() {
  return (
    <div className="rounded-2xl border border-[#3d3b3b] bg-gradient-to-br from-[#272626] via-[#242323] to-[#1e1d1d] p-6 lg:p-8 shadow-xl">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        {/* Core Description */}
        <div className="max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#FF8900]/10 border border-[#FF8900]/25 text-[#FF8900] text-xs font-semibold uppercase tracking-wider mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Core Mission</span>
          </div>

          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight leading-snug">
            Bridging the gap between real engineering evidence and job requirements.
          </h2>

          <p className="mt-3 text-sm text-[#aba5a5] leading-relaxed">
            Most career tools rely on unverified resume claims and buzzwords. <strong className="text-white font-medium">CareerProof AI</strong> grounds career guidance in reality by directly analyzing your <span className="text-[#FF8900] font-medium">GitHub portfolio codebase</span> and comparing proven technical competencies against target job descriptions.
          </p>
        </div>

        {/* 3 Step Evidence Loop Visual */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 lg:w-96 flex-shrink-0">
          <div className="bg-[#1c1b1b]/80 border border-[#383636] rounded-xl p-3.5 text-center">
            <div className="w-8 h-8 rounded-lg bg-[#2b2a2a] flex items-center justify-center mx-auto mb-2 text-[#FF8900]">
              <Code2 className="w-4 h-4" />
            </div>
            <p className="text-xs font-semibold text-white">1. GitHub Code</p>
            <p className="text-[11px] text-[#8a8585] mt-1">Commits, tests & PR patterns</p>
          </div>

          <div className="bg-[#1c1b1b]/80 border border-[#383636] rounded-xl p-3.5 text-center">
            <div className="w-8 h-8 rounded-lg bg-[#2b2a2a] flex items-center justify-center mx-auto mb-2 text-[#FF8900]">
              <FileSearch className="w-4 h-4" />
            </div>
            <p className="text-xs font-semibold text-white">2. Job Target</p>
            <p className="text-[11px] text-[#8a8585] mt-1">Real-world JD requirements</p>
          </div>

          <div className="bg-[#1c1b1b]/80 border border-[#383636] rounded-xl p-3.5 text-center">
            <div className="w-8 h-8 rounded-lg bg-[#2b2a2a] flex items-center justify-center mx-auto mb-2 text-[#FF8900]">
              <Target className="w-4 h-4" />
            </div>
            <p className="text-xs font-semibold text-white">3. Gap Radar</p>
            <p className="text-[11px] text-[#8a8585] mt-1">Evidence-backed roadmap</p>
          </div>
        </div>
      </div>
    </div>
  )
}
