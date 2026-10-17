import { useState, useMemo } from 'react'
import {
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Eye,
  FileCode,
  Tag,
  Cpu
} from 'lucide-react'
import EvidenceDetailModal from './EvidenceDetailModal'

export default function RequirementResultsTable({ results = [] }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [activeModalItem, setActiveModalItem] = useState(null)

  // Extract unique categories
  const categories = useMemo(() => {
    const set = new Set()
    results.forEach((r) => {
      if (r.category) set.add(r.category)
    })
    return Array.from(set).sort()
  }, [results])

  // Filtered list
  const filtered = useMemo(() => {
    return results.filter((item) => {
      // Search match
      const query = searchTerm.toLowerCase().trim()
      const matchesSearch =
        !query ||
        item.skill_name.toLowerCase().includes(query) ||
        (item.normalized_skill_name && item.normalized_skill_name.toLowerCase().includes(query)) ||
        (item.explanation && item.explanation.toLowerCase().includes(query)) ||
        (item.category && item.category.toLowerCase().includes(query))

      // Status match
      const matchesStatus =
        statusFilter === 'all' || item.status === statusFilter

      // Category match
      const matchesCategory =
        categoryFilter === 'all' || item.category === categoryFilter

      return matchesSearch && matchesStatus && matchesCategory
    })
  }, [results, searchTerm, statusFilter, categoryFilter])

  // Counts for status tabs
  const counts = useMemo(() => {
    return {
      all: results.length,
      demonstrated: results.filter((r) => r.status === 'demonstrated').length,
      partially_demonstrated: results.filter((r) => r.status === 'partially_demonstrated').length,
      not_demonstrated: results.filter((r) => r.status === 'not_demonstrated').length,
    }
  }, [results])

  return (
    <div className="space-y-4">
      {/* Search and Filters Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 rounded-xl bg-[#1e1d1d] border border-[#353333]">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-[#8c8888] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search skills, explanations, or technologies..."
            className="w-full bg-[#141414] border border-[#333131] rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-[#6d6a6a] focus:outline-none focus:border-[#FF8900] transition-colors"
          />
        </div>

        {/* Category Dropdown */}
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-[#8c8888]" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-[#141414] border border-[#333131] rounded-lg px-3 py-2 text-xs text-[#b0abab] focus:outline-none focus:border-[#FF8900]"
          >
            <option value="all">All Categories ({results.length})</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[#353333] pb-3 text-xs">
        <button
          onClick={() => setStatusFilter('all')}
          className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
            statusFilter === 'all'
              ? 'bg-[#FF8900]/15 text-[#FF8900] border border-[#FF8900]/30'
              : 'text-[#8c8888] hover:text-white hover:bg-[#2e2d2d]'
          }`}
        >
          All Requirements ({counts.all})
        </button>

        <button
          onClick={() => setStatusFilter('demonstrated')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-colors ${
            statusFilter === 'demonstrated'
              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
              : 'text-[#8c8888] hover:text-emerald-400 hover:bg-[#2e2d2d]'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Demonstrated ({counts.demonstrated})
        </button>

        <button
          onClick={() => setStatusFilter('partially_demonstrated')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-colors ${
            statusFilter === 'partially_demonstrated'
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
              : 'text-[#8c8888] hover:text-amber-400 hover:bg-[#2e2d2d]'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          Partially Demonstrated ({counts.partially_demonstrated})
        </button>

        <button
          onClick={() => setStatusFilter('not_demonstrated')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-colors ${
            statusFilter === 'not_demonstrated'
              ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
              : 'text-[#8c8888] hover:text-rose-400 hover:bg-[#2e2d2d]'
          }`}
        >
          <XCircle className="w-3.5 h-3.5" />
          Not Demonstrated ({counts.not_demonstrated})
        </button>
      </div>

      {/* Results Cards / Table */}
      {filtered.length === 0 ? (
        <div className="p-8 text-center rounded-xl bg-[#1e1d1d] border border-dashed border-[#353333] text-[#8c8888]">
          No job requirements matched the search or filter criteria.
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((item, idx) => {
            const evCount = (item.supporting_evidence || []).length

            return (
              <div
                key={item.id || idx}
                className="p-4 rounded-xl bg-[#201f1f] border border-[#353333] hover:border-[#4d4a4a] transition-all space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className="text-base font-bold text-white tracking-tight">
                      {item.skill_name}
                    </h4>

                    <span className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-[#2b2a2a] text-[#a49f9f] border border-[#3d3b3b]">
                      {item.category}
                    </span>

                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                        item.importance === 'required'
                          ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                          : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                      }`}
                    >
                      {item.importance === 'required' ? 'Required' : 'Preferred'}
                    </span>

                    {(item.rag_chunks_count > 0 || item.evaluation_method?.includes('rag') || (item.supporting_evidence || []).some(e => e.rag_retrieved)) && (
                      <span
                        title="Evaluated with ChromaDB Semantic Vector Retrieval"
                        className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-300 border border-purple-500/30"
                      >
                        <Cpu className="w-3 h-3 text-purple-400" />
                        RAG Verified
                      </span>
                    )}
                  </div>

                  {/* Status Badge */}
                  <div className="flex items-center gap-2">
                    {item.status === 'demonstrated' && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                        <CheckCircle2 className="w-3 h-3" /> Demonstrated
                      </span>
                    )}
                    {item.status === 'partially_demonstrated' && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                        <AlertTriangle className="w-3 h-3" /> Partially Demonstrated
                      </span>
                    )}
                    {item.status === 'not_demonstrated' && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                        <XCircle className="w-3 h-3" /> Not Demonstrated in Analyzed Files
                      </span>
                    )}
                  </div>
                </div>

                {/* Explanation */}
                <p className="text-xs text-[#b8b3b3] leading-relaxed">
                  {item.explanation}
                </p>

                {/* Footer Bar: Contribution, Evidence Count, Action Button */}
                <div className="pt-2 border-t border-[#2e2d2d] flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-3 text-[#8c8888]">
                    <span>
                      Score Contribution:{' '}
                      <strong className="text-white">
                        {item.score_contribution !== undefined ? `${item.score_contribution}%` : '0%'}
                      </strong>
                    </span>
                    <span>&bull;</span>
                    <span className="flex items-center gap-1">
                      <FileCode className="w-3.5 h-3.5 text-[#FF8900]" />
                      <strong className="text-[#dcd7d7]">{evCount}</strong> verified evidence {evCount === 1 ? 'item' : 'items'}
                    </span>
                  </div>

                  <button
                    onClick={() => setActiveModalItem(item)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#2b2a2a] hover:bg-[#383636] text-[#FF8900] hover:text-[#ffa333] font-semibold text-xs border border-[#3f3d3d] transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Inspect Evidence</span>
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Evidence Detail Modal */}
      {activeModalItem && (
        <EvidenceDetailModal
          item={activeModalItem}
          onClose={() => setActiveModalItem(null)}
        />
      )}
    </div>
  )
}
