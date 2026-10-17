import { AlertCircle, Target, ArrowRight, Layers, FileCheck, CheckCircle2 } from 'lucide-react'

export default function PrioritizedGapsSection({ gaps = [] }) {
  if (!gaps || gaps.length === 0) {
    return (
      <div className="p-8 text-center rounded-2xl bg-[#1e1d1d] border border-emerald-500/20 text-emerald-400 space-y-2">
        <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-400">
          <CheckCircle2 className="w-5 h-5" />
        </div>
        <h4 className="text-base font-bold text-white">No Critical Skill Gaps Identified!</h4>
        <p className="text-xs text-[#b0abab] max-w-md mx-auto">
          All analyzed job requirements have direct technical evidence verified across your selected repositories.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Target className="w-5 h-5 text-[#FF8900]" />
            Prioritized Skill Gaps ({gaps.length})
          </h3>
          <p className="text-xs text-[#8c8888] mt-0.5">
            Ranked deterministically by requirement importance and lack of verified repository evidence.
          </p>
        </div>

        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
          Focus Areas
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {gaps.map((gap, idx) => (
          <div
            key={gap.requirement_id || idx}
            className="p-5 rounded-2xl bg-[#1f1e1e] border border-[#353333] hover:border-[#4d4a4a] transition-all space-y-3.5 relative overflow-hidden"
          >
            {/* Gap Rank Banner */}
            <div className="flex items-center justify-between text-xs">
              <span className="font-mono font-bold text-[#FF8900] bg-[#FF8900]/10 px-2 py-0.5 rounded border border-[#FF8900]/25">
                Priority Rank #{idx + 1}
              </span>

              <div className="flex items-center gap-1.5">
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                    gap.importance === 'required'
                      ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                      : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                  }`}
                >
                  {gap.importance === 'required' ? 'Required Skill' : 'Preferred Skill'}
                </span>

                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                    gap.status === 'not_demonstrated'
                      ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                      : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {gap.status === 'not_demonstrated' ? 'No Evidence Found' : 'Partial Evidence'}
                </span>
              </div>
            </div>

            {/* Skill Title & Category */}
            <div>
              <h4 className="text-base font-bold text-white tracking-tight">
                {gap.skill_name}
              </h4>
              <span className="text-[11px] text-[#8c8888]">{gap.category}</span>
            </div>

            {/* Why Evidence is Insufficient */}
            <div className="p-3 rounded-xl bg-[#262525] border border-[#353333] text-xs text-[#b8b3b3] space-y-1">
              <span className="font-semibold text-rose-400/90 text-[11px] uppercase tracking-wider block">
                Deficiency Reason:
              </span>
              <p>{gap.gap_reason}</p>
              {gap.existing_evidence_summary && (
                <p className="text-[11px] text-amber-300/80 pt-1 border-t border-[#353333]">
                  <strong>Existing mention:</strong> {gap.existing_evidence_summary}
                </p>
              )}
            </div>

            {/* Actionable Suggestion */}
            <div className="space-y-1 text-xs">
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <ArrowRight className="w-3.5 h-3.5" /> Suggested Action:
              </span>
              <p className="text-[#dcd7d7] pl-4">{gap.suggested_action}</p>
            </div>

            {/* Expected Artifact */}
            <div className="pt-2 border-t border-[#2d2c2c] flex items-start gap-2 text-xs text-[#8c8888]">
              <FileCheck className="w-3.5 h-3.5 text-[#FF8900] shrink-0 mt-0.5" />
              <span>
                <strong className="text-[#b0abab]">Expected Portfolio Artifact:</strong>{' '}
                {gap.expected_artifact}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
