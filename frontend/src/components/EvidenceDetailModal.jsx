import { X, ExternalLink, FileCode, CheckCircle2, AlertTriangle, XCircle, ShieldAlert, GitCommit, Cpu, Database, Layers } from 'lucide-react'

export default function EvidenceDetailModal({ item, onClose }) {
  if (!item) return null

  const evidenceList = item.supporting_evidence || []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#1f1e1e] border border-[#383636] rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 border-b border-[#353333] flex items-start justify-between gap-4 bg-[#1a1919]">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#353333] text-[#b0abab] border border-[#444]">
                {item.category}
              </span>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                item.importance === 'required'
                  ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                  : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
              }`}>
                {item.importance === 'required' ? 'Required' : 'Preferred'}
              </span>
            </div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              {item.skill_name}
              {item.normalized_skill_name && item.normalized_skill_name !== item.skill_name && (
                <span className="text-xs font-normal text-[#8c8888]">
                  (Normalized: {item.normalized_skill_name})
                </span>
              )}
            </h3>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#8c8888] hover:text-white hover:bg-[#333131] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm">
          {/* Status & Explanation Box */}
          <div className="p-4 rounded-xl bg-[#272626] border border-[#383636] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#8c8888]">
                Assessment Evaluation
              </span>
              {item.status === 'demonstrated' && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Demonstrated
                </span>
              )}
              {item.status === 'partially_demonstrated' && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                  <AlertTriangle className="w-3.5 h-3.5" /> Partially Demonstrated
                </span>
              )}
              {item.status === 'not_demonstrated' && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                  <XCircle className="w-3.5 h-3.5" /> Not Demonstrated in Analyzed Files
                </span>
              )}
            </div>

            <p className="text-[#dcd7d7] leading-relaxed">
              {item.explanation}
            </p>

            {item.limitations && (
              <div className="flex items-start gap-2 text-xs text-amber-300/90 pt-1 border-t border-[#383636]">
                <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
                <span>{item.limitations}</span>
              </div>
            )}
          </div>

          {/* RAG Vector Retrieval Status Card */}
          {(item.evaluation_method?.includes('rag') || item.rag_chunks_count > 0 || evidenceList.some((e) => e.rag_retrieved)) && (
            <div className="p-3.5 rounded-xl bg-purple-950/25 border border-purple-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-purple-900/40 border border-purple-700/50">
                  <Database className="w-4 h-4 text-purple-300" />
                </div>
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <span>ChromaDB Vector Retrieval Pipeline</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      RAG Verified
                    </span>
                  </div>
                  <p className="text-[11px] text-purple-200/80 m-0">
                    Semantic cosine distance match against language-aware indexed repository code chunks.
                  </p>
                </div>
              </div>

              {item.rag_chunks_count > 0 && (
                <div className="text-right flex-shrink-0">
                  <span className="text-xs font-mono font-bold text-purple-300 px-2 py-1 rounded bg-purple-900/60 border border-purple-700/60">
                    {item.rag_chunks_count} {item.rag_chunks_count === 1 ? 'Chunk' : 'Chunks'} Indexed
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Supporting Evidence List */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#8c8888] mb-3 flex items-center justify-between">
              <span>Verified Evidence Records ({evidenceList.length})</span>
              <span className="text-[11px] text-[#FF8900] normal-case font-normal">
                Direct Repository Evidence Snapshots
              </span>
            </h4>

            {evidenceList.length === 0 ? (
              <div className="p-5 text-center rounded-xl bg-[#242323] border border-dashed border-[#383636] text-[#8c8888]">
                No code or test evidence was detected in the selected repositories for this requirement.
              </div>
            ) : (
              <div className="space-y-4">
                {evidenceList.map((ev, idx) => (
                  <div
                    key={ev.id || idx}
                    className="p-4 rounded-xl bg-[#242323] border border-[#383636] space-y-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white px-2 py-0.5 rounded bg-[#333131] border border-[#444]">
                          {ev.repository_name || 'Repository'}
                        </span>
                        <span className="text-[#b0abab] font-mono flex items-center gap-1">
                          <FileCode className="w-3.5 h-3.5 text-[#FF8900]" />
                          {ev.file_path || 'Source file'}
                        </span>
                        {ev.line_start && (
                          <span className="text-[#8c8888] font-mono text-[11px]">
                            L{ev.line_start}{ev.line_end && ev.line_end !== ev.line_start ? `-L${ev.line_end}` : ''}
                          </span>
                        )}
                        {ev.rag_retrieved && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1">
                            <Cpu className="w-3 h-3 text-purple-400" />
                            RAG Chunk
                          </span>
                        )}
                      </div>

                      {ev.github_url && (
                        <a
                          href={ev.github_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-[#FF8900] hover:text-[#ffa333] transition-colors"
                        >
                          <GitCommit className="w-3 h-3" />
                          <span>View on GitHub</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>

                    <p className="text-xs text-[#dcd7d7]">
                      {ev.evidence_summary}
                    </p>

                    {/* Code Excerpt Snippet */}
                    {ev.code_excerpt && (
                      <div className="relative rounded-lg bg-[#141414] border border-[#2e2d2d] overflow-hidden">
                        <div className="px-3 py-1 bg-[#1a1919] border-b border-[#2e2d2d] text-[10px] text-[#8c8888] font-mono flex items-center justify-between">
                          <span>Verified Code Excerpt</span>
                          {ev.commit_sha && (
                            <span className="text-[#6d6a6a]">SHA: {ev.commit_sha.substring(0, 7)}</span>
                          )}
                        </div>
                        <pre className="p-3 text-[11px] font-mono text-[#4ade80] overflow-x-auto whitespace-pre leading-relaxed">
                          {ev.code_excerpt}
                        </pre>
                      </div>
                    )}

                    <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#8c8888] pt-1 border-t border-[#2e2d2d]">
                      <div className="flex items-center gap-3">
                        <span>Type: <strong className="text-[#b0abab]">{ev.chunk_type || ev.evidence_type}</strong></span>
                        {ev.language && (
                          <span>Language: <strong className="text-[#b0abab]">{ev.language}</strong></span>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        {ev.relevance_score !== undefined && (
                          <span>Relevance: <strong className="text-purple-300 font-mono">{Math.round(ev.relevance_score * 100)}%</strong></span>
                        )}
                        {ev.retrieval_distance !== undefined && (
                          <span>Distance: <strong className="text-[#aaa] font-mono">{Number(ev.retrieval_distance).toFixed(3)}</strong></span>
                        )}
                        {ev.confidence !== undefined && ev.relevance_score === undefined && (
                          <span>Confidence: <strong className="text-emerald-400">{(ev.confidence * 100).toFixed(0)}%</strong></span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Suggested Next Step */}
          {item.suggested_next_step && (
            <div className="p-4 rounded-xl bg-[#2a241b] border border-[#FF8900]/30 space-y-1">
              <span className="text-xs font-semibold text-[#FF8900] uppercase tracking-wider">
                Recommended Action to Strengthen Portfolio
              </span>
              <p className="text-xs text-[#dcd7d7]">
                {item.suggested_next_step}
              </p>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-[#353333] bg-[#1a1919] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-lg bg-[#333131] hover:bg-[#3d3a3a] text-white text-xs font-semibold transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  )
}
