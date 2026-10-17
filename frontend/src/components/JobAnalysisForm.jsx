import { useState } from 'react'
import { FileText, Sparkles, AlertCircle, Loader2 } from 'lucide-react'

export default function JobAnalysisForm({ onSubmit, isAnalyzing, currentStage }) {
  const [pastedDescription, setPastedDescription] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [validationError, setValidationError] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    setValidationError('')

    if (!pastedDescription || pastedDescription.trim().length < 50) {
      setValidationError('Please paste sufficient job description text (minimum 50 characters).')
      return
    }

    onSubmit({
      pasted_description: pastedDescription.trim(),
      job_title: jobTitle.trim() || null,
      company_name: companyName.trim() || null,
    })
  }

  return (
    <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-6 shadow-xl">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2 m-0">
          <Sparkles className="w-5 h-5 text-[#FF8900]" />
          Analyze Job Requirements
        </h2>
        <p className="text-sm text-[#b0abab] mt-1 m-0">
          Paste the job description below to extract structured technical requirements.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Optional Metadata Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-[#d4cfcf] mb-1">
              Job Title <span className="text-[#888] font-normal">(optional)</span>
            </label>
            <input
              type="text"
              disabled={isAnalyzing}
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g. Backend Developer Intern"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#232222] border border-[#3a3838] text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#FF8900] transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[#d4cfcf] mb-1">
              Company Name <span className="text-[#888] font-normal">(optional)</span>
            </label>
            <input
              type="text"
              disabled={isAnalyzing}
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g. Stripe, Google, or Startup"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#232222] border border-[#3a3838] text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#FF8900] transition-colors"
            />
          </div>
        </div>

        {/* Job Description Textarea */}
        <div>
          <label className="block text-xs font-medium text-[#d4cfcf] mb-1">
            Job Description <span className="text-rose-400">*</span>
          </label>
          <textarea
            rows={8}
            disabled={isAnalyzing}
            value={pastedDescription}
            onChange={(e) => setPastedDescription(e.target.value)}
            placeholder="Paste the complete responsibilities, qualifications, and requirements from the job posting..."
            className="w-full p-3.5 rounded-xl bg-[#232222] border border-[#3a3838] text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#FF8900] transition-colors resize-y"
          />
          <div className="flex items-center justify-between text-[11px] text-[#888] mt-1">
            <span>Authoritative text source for extraction</span>
            <span>{pastedDescription.length} characters (min 50)</span>
          </div>
        </div>

        {/* Validation Error Message */}
        {validationError && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{validationError}</span>
          </div>
        )}

        {/* Action Button & Active Progress */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-xs text-[#9c9797]">
            {isAnalyzing && (
              <span className="flex items-center gap-2 text-[#FF8900] font-medium">
                <Loader2 className="w-4 h-4 animate-spin" />
                {currentStage || 'Processing requirement analysis...'}
              </span>
            )}
          </div>
          <button
            type="submit"
            disabled={isAnalyzing}
            className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-[#FF8900] hover:bg-[#e07900] disabled:opacity-50 text-white font-semibold text-sm transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2 cursor-pointer border-none"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing Job...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Extract Requirements
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
