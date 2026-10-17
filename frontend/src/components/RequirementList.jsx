import { useMemo, useState } from 'react'
import {
  Code2,
  Layers,
  Server,
  Database,
  CheckCircle2,
  Cloud,
  Wrench,
  Brain,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Tag,
  Building,
  Briefcase,
  Quote,
} from 'lucide-react'

const CATEGORY_CONFIG = {
  'Programming languages': {
    icon: Code2,
    color: 'text-sky-400',
    badgeBg: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  },
  'Frameworks and libraries': {
    icon: Layers,
    color: 'text-violet-400',
    badgeBg: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  },
  'Backend and API development': {
    icon: Server,
    color: 'text-emerald-400',
    badgeBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  },
  'Databases and data management': {
    icon: Database,
    color: 'text-amber-400',
    badgeBg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  },
  'Testing and quality assurance': {
    icon: CheckCircle2,
    color: 'text-teal-400',
    badgeBg: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  },
  'Deployment and DevOps': {
    icon: Cloud,
    color: 'text-cyan-400',
    badgeBg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  },
  'Tools and platforms': {
    icon: Wrench,
    color: 'text-orange-400',
    badgeBg: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  },
  'Core concepts and soft skills': {
    icon: Brain,
    color: 'text-pink-400',
    badgeBg: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  },
}

export default function RequirementList({ job, onNewAnalysis }) {
  const [activeCategory, setActiveCategory] = useState('all')
  const [showOriginalSource, setShowOriginalSource] = useState(false)

  // Group requirements by category
  const groupedRequirements = useMemo(() => {
    const groups = {}
    const reqs = job?.requirements || []
    reqs.forEach((r) => {
      const cat = r.category || 'Core concepts and soft skills'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(r)
    })
    return groups
  }, [job])

  const categories = Object.keys(CATEGORY_CONFIG)

  const filteredRequirements = useMemo(() => {
    const reqs = job?.requirements || []
    if (activeCategory === 'all') return reqs
    return reqs.filter((r) => r.category === activeCategory)
  }, [job, activeCategory])

  if (!job) return null

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-[#FF8900]/15 text-[#FF8900] border border-[#FF8900]/30 flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5" />
                {job.job_title || 'Position Analysis'}
              </span>
              {job.company_name && (
                <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#2a2929] text-[#d4cfcf] border border-[#3a3838] flex items-center gap-1.5">
                  <Building className="w-3.5 h-3.5 text-[#9c9797]" />
                  {job.company_name}
                </span>
              )}
              <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-[#2a2929] text-[#9c9797] border border-[#3a3838]">
                {job.requirements?.length || 0} requirements extracted
              </span>
            </div>

            <h1 className="text-2xl font-bold text-white m-0">
              {job.job_title || 'Analyzed Job Requirements'}
            </h1>

            {job.summary && (
              <p className="text-sm text-[#b0abab] max-w-3xl leading-relaxed m-0 pt-1">
                {job.summary}
              </p>
            )}

            {job.source_url && (
              <div className="pt-1">
                <a
                  href={job.source_url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="inline-flex items-center gap-1.5 text-xs text-[#FF8900] hover:text-[#ff9d2e] underline transition-colors"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  View Original Posting URL
                </a>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 self-start">
            <button
              onClick={() => setShowOriginalSource(!showOriginalSource)}
              className="px-3.5 py-2 rounded-xl bg-[#2a2929] hover:bg-[#333131] border border-[#3a3838] text-xs font-medium text-[#d4cfcf] hover:text-white transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              {showOriginalSource ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              {showOriginalSource ? 'Hide Full Source' : 'View Full Source'}
            </button>
            {onNewAnalysis && (
              <button
                onClick={onNewAnalysis}
                className="px-3.5 py-2 rounded-xl bg-[#FF8900] hover:bg-[#e07900] text-xs font-semibold text-white transition-colors cursor-pointer border-none"
              >
                + New Analysis
              </button>
            )}
          </div>
        </div>

        {/* Collapsible Source Text */}
        {showOriginalSource && (
          <div className="mt-6 pt-5 border-t border-[#353333]">
            <h4 className="text-xs font-semibold text-[#b0abab] uppercase tracking-wider mb-2">
              Original Job Description Text
            </h4>
            <div className="bg-[#232222] border border-[#353333] rounded-xl p-4 max-h-80 overflow-y-auto text-xs text-[#d4cfcf] whitespace-pre-wrap font-mono leading-relaxed">
              {job.description}
            </div>
          </div>
        )}
      </div>

      {/* Category Filter Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        <button
          onClick={() => setActiveCategory('all')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer flex-shrink-0 ${
            activeCategory === 'all'
              ? 'bg-[#FF8900] text-white'
              : 'bg-[#1a1919] border border-[#353333] text-[#b0abab] hover:text-white'
          }`}
        >
          All Skills ({job.requirements?.length || 0})
        </button>
        {categories.map((cat) => {
          const count = groupedRequirements[cat]?.length || 0
          if (count === 0) return null
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer flex-shrink-0 flex items-center gap-1.5 ${
                activeCategory === cat
                  ? 'bg-[#FF8900] text-white'
                  : 'bg-[#1a1919] border border-[#353333] text-[#b0abab] hover:text-white'
              }`}
            >
              <span>{cat}</span>
              <span className="text-[10px] opacity-75">({count})</span>
            </button>
          )
        })}
      </div>

      {/* Structured Requirements Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredRequirements.map((req) => {
          const cfg = CATEGORY_CONFIG[req.category] || CATEGORY_CONFIG['Core concepts and soft skills']
          const Icon = cfg.icon || Tag
          const isRequired = req.importance === 'required'

          return (
            <div
              key={req.id || `${req.skill_name}-${req.category}`}
              className="bg-[#1a1919] border border-[#353333] rounded-xl p-4 hover:border-[#4a4747] transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-[#2a2929] border border-[#3a3838]">
                      <Icon className={`w-4 h-4 ${cfg.color}`} />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-white m-0">
                        {req.skill_name}
                      </h3>
                      <span className="text-[11px] text-[#888]">{req.category}</span>
                    </div>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${
                      isRequired
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    }`}
                  >
                    {req.importance || 'required'}
                  </span>
                </div>

                {req.description && (
                  <p className="text-xs text-[#c9c5c5] leading-relaxed mb-3 m-0">
                    {req.description}
                  </p>
                )}
              </div>

              {req.source_excerpt && (
                <div className="mt-2 pt-2 border-t border-[#2e2d2d] bg-[#232222]/50 rounded-lg p-2.5">
                  <div className="flex items-start gap-1.5">
                    <Quote className="w-3.5 h-3.5 text-[#FF8900] flex-shrink-0 mt-0.5" />
                    <p className="text-[11px] text-[#9c9797] italic m-0 line-clamp-3">
                      "{req.source_excerpt}"
                    </p>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {filteredRequirements.length === 0 && (
        <div className="text-center py-12 bg-[#1a1919] border border-[#353333] rounded-2xl">
          <p className="text-sm text-[#888] m-0">No requirements found in this category.</p>
        </div>
      )}
    </div>
  )
}
