import { BarChart3, BookOpen, GitBranch, Lock, Terminal } from 'lucide-react'

export default function SkillGapPreviewSection() {
  const previewModules = [
    {
      title: 'GitHub Portfolio Evidence Harvester',
      badge: 'Core Service',
      icon: GitBranch,
      description:
        'Connects to GitHub API to inspect public repositories, commit cadence, test suites, architecture decisions, and code complexity metrics.',
      capabilities: [
        'Commit history and frequency analyzer',
        'Language and framework depth validation',
        'Automated test coverage verification',
      ],
    },
    {
      title: 'Target Job Description Parser',
      badge: 'Core Service',
      icon: BookOpen,
      description:
        'Extracts structured technical competencies, required seniorities, and framework expectations from raw job postings using targeted LLM prompts.',
      capabilities: [
        'Must-have vs. nice-to-have skill categorization',
        'Seniority baseline mapping',
        'Domain-specific library extraction',
      ],
    },
    {
      title: 'Evidence-Based Skill Gap Engine',
      badge: 'Assessment Engine',
      icon: BarChart3,
      description:
        'Calculates objective delta between candidate proven repository evidence and employer requirements. No simulated scores or fabricated metrics.',
      capabilities: [
        'Evidence confidence scoring based on actual code',
        'Deficiency breakdown with concrete code examples',
        'Blind spot detection for production readiness',
      ],
    },
    {
      title: 'Actionable Engineering Career Roadmap',
      badge: 'Assessment Engine',
      icon: Terminal,
      description:
        'Generates concrete repo enhancements, architectural exercises, and project ideas specifically designed to produce missing portfolio evidence.',
      capabilities: [
        'Step-by-step project implementation guides',
        'Open-source contribution recommendations',
        'Continuous repository milestone monitoring',
      ],
    },
  ]

  return (
    <section className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#353333] pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-white tracking-tight m-0">
              Skill-Gap Analysis Engine
            </h2>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-[#333131] text-[#b8b3b3] border border-[#484545]">
              AI Capability Overview
            </span>
          </div>
          <p className="text-xs text-[#9c9797] mt-1">
            Engine architecture designed for transparent evidence verification, comparing real repository artifacts with employer requirements.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/20 font-medium">
          <Lock className="w-3.5 h-3.5" />
          <span>Active & Integrated</span>
        </div>
      </div>

      {/* Grid of Preview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {previewModules.map((module) => {
          const Icon = module.icon
          return (
            <div
              key={module.title}
              className="rounded-xl border border-[#383636] bg-[#272626]/70 p-5 relative overflow-hidden group hover:border-[#4d4a4a] transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-[#1f1e1e] border border-[#383636] text-[#FF8900]">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white tracking-tight">
                      {module.title}
                    </h3>
                    <span className="text-[10px] font-mono text-[#a19c9c]">
                      {module.badge}
                    </span>
                  </div>
                </div>

                <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-[#1f1e1e] text-[#8e8989] border border-[#363434]">
                  Pending Activation
                </span>
              </div>

              <p className="text-xs text-[#a8a3a3] mt-3 leading-relaxed">
                {module.description}
              </p>

              <div className="mt-4 pt-3 border-t border-[#333131]">
                <p className="text-[11px] font-medium text-[#7a7575] uppercase tracking-wider mb-2">
                  Planned Capabilities
                </p>
                <ul className="space-y-1.5">
                  {module.capabilities.map((cap, i) => (
                    <li
                      key={i}
                      className="text-xs text-[#cfc9c9] flex items-center space-x-2"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-[#FF8900]/60 flex-shrink-0" />
                      <span>{cap}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
