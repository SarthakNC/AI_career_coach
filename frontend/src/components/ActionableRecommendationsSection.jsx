import { Sparkles, Clock, GitBranch, ArrowUpRight, CheckSquare, Layers } from 'lucide-react'

export default function ActionableRecommendationsSection({ recommendations = [] }) {
  if (!recommendations || recommendations.length === 0) {
    return null
  }

  // Group by priority
  const priorityOrder = { high: 1, medium: 2, low: 3 }
  const sorted = [...recommendations].sort((a, b) => {
    const pA = priorityOrder[a.priority?.toLowerCase()] || 2
    const pB = priorityOrder[b.priority?.toLowerCase()] || 2
    return pA - pB
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#FF8900]" />
            Actionable Portfolio Recommendations ({recommendations.length})
          </h3>
          <p className="text-xs text-[#8c8888] mt-0.5">
            Grounded improvements tailored to bridge gaps in your analyzed repositories.
          </p>
        </div>

        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-[#FF8900]/10 text-[#FF8900] border border-[#FF8900]/25">
          Grounded Action Plan
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sorted.map((rec, idx) => {
          const priority = (rec.priority || 'medium').toLowerCase()

          let priorityBadge = (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Medium Priority
            </span>
          )
          if (priority === 'high') {
            priorityBadge = (
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-400 border border-rose-500/30">
                High Priority
              </span>
            )
          } else if (priority === 'low') {
            priorityBadge = (
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-zinc-500/15 text-zinc-400 border border-zinc-500/30">
                Low Priority
              </span>
            )
          }

          return (
            <div
              key={rec.id || idx}
              className="p-5 rounded-2xl bg-[#1f1e1e] border border-[#353333] hover:border-[#4d4a4a] transition-all space-y-3 relative overflow-hidden"
            >
              <div className="flex items-center justify-between text-xs">
                {priorityBadge}

                {rec.estimated_effort && (
                  <span className="flex items-center gap-1 text-[11px] font-mono text-[#8c8888]">
                    <Clock className="w-3 h-3 text-[#FF8900]" />
                    {rec.estimated_effort}
                  </span>
                )}
              </div>

              {/* Title */}
              <h4 className="text-base font-bold text-white tracking-tight leading-snug">
                {rec.title}
              </h4>

              {/* Reason */}
              <p className="text-xs text-[#b8b3b3]">
                {rec.reason}
              </p>

              {/* Concrete Suggested Task */}
              <div className="p-3 rounded-xl bg-[#262525] border border-[#353333] space-y-2 text-xs">
                <div>
                  <span className="font-semibold text-white text-[11px] flex items-center gap-1.5">
                    <CheckSquare className="w-3.5 h-3.5 text-emerald-400" /> Suggested Implementation Task:
                  </span>
                  <p className="text-[#dcd7d7] mt-1 pl-5">
                    {rec.suggested_task}
                  </p>
                </div>

                <div className="pt-2 border-t border-[#333131]">
                  <span className="font-semibold text-white text-[11px] flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-[#FF8900]" /> Expected Artifact:
                  </span>
                  <p className="text-[#a49f9f] mt-0.5 pl-5 font-mono text-[11px]">
                    {rec.expected_artifact}
                  </p>
                </div>
              </div>

              {/* Related Repository Badge */}
              <div className="pt-2 border-t border-[#2e2d2d] flex items-center justify-between text-xs text-[#8c8888]">
                {rec.related_repository_name ? (
                  <span className="flex items-center gap-1 text-[#b0abab]">
                    <GitBranch className="w-3.5 h-3.5 text-[#FF8900]" /> Target Repository:{' '}
                    <strong className="text-white font-mono">{rec.related_repository_name}</strong>
                  </span>
                ) : (
                  <span className="text-[#8c8888]">General Portfolio Enhancement</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
