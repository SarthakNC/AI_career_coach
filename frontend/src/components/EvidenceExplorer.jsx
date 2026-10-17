import { useState, useMemo } from 'react'
import {
  Code2,
  ExternalLink,
  Search,
  FileCode,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

const STATUS_CONFIG = {
  'Strong evidence': {
    badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25',
    bar: 'bg-emerald-500',
  },
  'Some evidence': {
    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/25',
    bar: 'bg-amber-500',
  },
  'Mentioned only': {
    badge: 'bg-sky-500/10 text-sky-400 border-sky-500/25',
    bar: 'bg-sky-500',
  },
  'Not demonstrated in analyzed files': {
    badge: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/25',
    bar: 'bg-zinc-500',
  },
}

export default function EvidenceExplorer({ evidence, repoFullName }) {
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedType, setSelectedType] = useState('all')
  const [expandedId, setExpandedId] = useState(null)

  const categories = useMemo(() => {
    const set = new Set()
    evidence.forEach((e) => e.category && set.add(e.category))
    return Array.from(set)
  }, [evidence])

  const types = useMemo(() => {
    const set = new Set()
    evidence.forEach((e) => e.evidence_type && set.add(e.evidence_type))
    return Array.from(set)
  }, [evidence])

  const filteredEvidence = useMemo(() => {
    return evidence.filter((item) => {
      const matchSearch =
        item.skill_name.toLowerCase().includes(search.toLowerCase()) ||
        (item.evidence_summary || '').toLowerCase().includes(search.toLowerCase()) ||
        (item.file_path || '').toLowerCase().includes(search.toLowerCase())

      const matchCategory = selectedCategory === 'all' || item.category === selectedCategory
      const matchType = selectedType === 'all' || item.evidence_type === selectedType

      return matchSearch && matchCategory && matchType
    })
  }, [evidence, search, selectedCategory, selectedType])

  return (
    <div className="space-y-5">
      {/* Search and Filters */}
      <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-4 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search skills, files, or summary..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-[#232222] border border-[#3a3838] text-sm text-white placeholder-[#777] focus:outline-none focus:border-[#FF8900]"
          />
          <Search className="w-4 h-4 text-[#888] absolute left-3 top-2.5" />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 rounded-xl bg-[#232222] border border-[#3a3838] text-xs text-[#d4cfcf] focus:outline-none focus:border-[#FF8900] cursor-pointer"
          >
            <option value="all">All Categories ({categories.length})</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 rounded-xl bg-[#232222] border border-[#3a3838] text-xs text-[#d4cfcf] focus:outline-none focus:border-[#FF8900] cursor-pointer"
          >
            <option value="all">All Evidence Types ({types.length})</option>
            {types.map((t) => (
              <option key={t} value={t}>
                {t.replace('_', ' ')}
              </option>
            ))}
          </select>

          <span className="text-xs text-[#888] ml-2">
            Showing <strong className="text-white">{filteredEvidence.length}</strong> of {evidence.length}
          </span>
        </div>
      </div>

      {/* Evidence Cards */}
      <div className="space-y-3">
        {filteredEvidence.map((item, idx) => {
          const cfg = STATUS_CONFIG[item.status_label] || STATUS_CONFIG['Some evidence']
          const isExpanded = expandedId === idx || (idx === 0 && expandedId === null)

          return (
            <div
              key={item.id || `${item.skill_name}-${idx}`}
              className="bg-[#1a1919] border border-[#353333] hover:border-[#444] rounded-2xl p-5 transition-all shadow-md"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-xl bg-[#232222] border border-[#353333] mt-0.5">
                    <Code2 className="w-5 h-5 text-[#FF8900]" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-base font-bold text-white m-0">{item.skill_name}</h4>
                      <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#2a2929] text-[#b0abab] border border-[#3a3838]">
                        {item.category}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono text-[#999] bg-[#232222] border border-[#353333]">
                        {item.evidence_type}
                      </span>
                    </div>

                    <p className="text-xs text-[#d4cfcf] mt-1 m-0 leading-relaxed max-w-2xl">
                      {item.evidence_summary}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-center">
                  <div className="text-right">
                    <span
                      className={`inline-block px-2.5 py-1 rounded-lg text-xs font-semibold border ${cfg.badge}`}
                    >
                      {item.status_label}
                    </span>
                    <div className="text-[10px] text-[#888] mt-0.5">
                      Confidence: {Math.round((item.confidence || 0.8) * 100)}%
                    </div>
                  </div>

                  <button
                    onClick={() => setExpandedId(isExpanded ? -1 : idx)}
                    className="p-1.5 rounded-lg bg-[#2a2929] hover:bg-[#333] text-[#d4cfcf] border border-[#3a3838] transition-colors cursor-pointer"
                    title={isExpanded ? 'Collapse excerpt' : 'View code excerpt'}
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Verified File Reference & Excerpt */}
              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-[#2e2d2d] space-y-3">
                  {item.file_path && (
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-[#b0abab] bg-[#232222] px-3.5 py-2 rounded-xl border border-[#353333]">
                      <div className="flex items-center gap-2 truncate">
                        <FileCode className="w-4 h-4 text-[#FF8900] flex-shrink-0" />
                        <span className="font-mono text-white truncate">{item.file_path}</span>
                        {item.line_start && (
                          <span className="text-[#888]">
                            (lines {item.line_start}
                            {item.line_end ? `–${item.line_end}` : ''})
                          </span>
                        )}
                      </div>

                      {item.github_url && (
                        <a
                          href={item.github_url}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="inline-flex items-center gap-1 text-[#FF8900] hover:text-[#ff9f30] font-medium transition-colors"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>View on GitHub</span>
                        </a>
                      )}
                    </div>
                  )}

                  {/* Verified Code Excerpt */}
                  {item.code_excerpt && (
                    <div className="relative">
                      <div className="bg-[#121212] border border-[#2e2d2d] rounded-xl p-3.5 text-xs text-[#e6e1e1] font-mono whitespace-pre overflow-x-auto max-h-56 leading-relaxed">
                        {item.code_excerpt}
                      </div>
                    </div>
                  )}

                  {/* Limitations and Honest Assessment */}
                  {item.limitations && (
                    <div className="flex items-start gap-2 p-2.5 rounded-xl bg-amber-500/5 border border-amber-500/15 text-amber-300 text-xs">
                      <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <strong className="font-semibold">Evidence Limitation: </strong>
                        <span className="text-amber-200/90">{item.limitations}</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}

        {filteredEvidence.length === 0 && (
          <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-8 text-center text-sm text-[#888]">
            No skill evidence matched the filter criteria.
          </div>
        )}
      </div>
    </div>
  )
}
