/**
 * ComingSoonPage — Generic placeholder for features not yet implemented.
 */
import { Lock } from 'lucide-react'
import { useLocation } from 'react-router-dom'

const pageMeta = {
  '/dashboard/jobs': {
    title: 'Job Analysis',
    description: 'Parse real job postings to extract technical requirements, seniority expectations, and framework demands.',
    phase: 'Phase 5',
  },
  '/dashboard/github': {
    title: 'GitHub Portfolio',
    description: 'Connect your GitHub profile so the platform can inspect repositories, commit patterns, test coverage, and code quality.',
    phase: 'Phase 5',
  },
  '/dashboard/skills': {
    title: 'Skill Gaps',
    description: 'Evidence-based skill-gap assessment comparing your proven repository evidence against employer requirements.',
    phase: 'Phase 5',
  },
  '/dashboard/history': {
    title: 'Assessment History',
    description: 'View past assessments and track how your skill profile evolves as you push code updates.',
    phase: 'Phase 5',
  },
  '/dashboard/settings': {
    title: 'Settings',
    description: 'Account preferences, notification settings, and connected service configuration.',
    phase: 'Phase 5',
  },
}

export default function ComingSoonPage() {
  const location = useLocation()
  const meta = pageMeta[location.pathname] || {
    title: 'Coming Soon',
    description: 'This feature is under development.',
    phase: 'Future',
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col items-center justify-center py-20 text-center">
      <div className="w-16 h-16 rounded-2xl bg-[#FF8900]/10 border border-[#FF8900]/25 flex items-center justify-center mb-6">
        <Lock className="w-8 h-8 text-[#FF8900]" />
      </div>

      <h1 className="text-2xl font-bold text-white mb-2">{meta.title}</h1>
      <p className="text-sm text-[#a8a3a3] leading-relaxed max-w-md mb-4">
        {meta.description}
      </p>

      <span className="text-[11px] uppercase font-semibold px-3 py-1 rounded-full bg-[#333131] text-[#b0abab] border border-[#484545] tracking-wider">
        Planned for {meta.phase}
      </span>
    </div>
  )
}
