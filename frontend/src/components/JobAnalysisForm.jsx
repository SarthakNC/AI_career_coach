import { useState } from 'react'
import { Globe, FileText, Sparkles, AlertCircle, Loader2 } from 'lucide-react'

export default function JobAnalysisForm({ onSubmit, isAnalyzing, currentStage }) {
  const [inputMode, setInputMode] = useState('url') // 'url' | 'paste'
  const [jobUrl, setJobUrl] = useState('')
  const [pastedDescription, setPastedDescription] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [validationError, setValidationError] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    setValidationError('')

    if (inputMode === 'url') {
      if (!jobUrl || !jobUrl.trim()) {
        setValidationError('Please enter a public job posting URL.')
        return
      }
      try {
        const parsed = new URL(jobUrl.trim())
        if (!['http:', 'https:'].includes(parsed.protocol)) {
          setValidationError('Please enter a valid HTTP or HTTPS URL.')
          return
        }
      } catch {
        setValidationError('Invalid URL format. Please include http:// or https://.')
        return
      }
    } else {
      if (!pastedDescription || pastedDescription.trim().length < 50) {
        setValidationError('Please paste sufficient job description text (minimum 50 characters).')
        return
      }
    }

    onSubmit({
      job_url: jobUrl.trim() || null,
      pasted_description: pastedDescription.trim() || null,
      job_title: jobTitle.trim() || null,
      company_name: companyName.trim() || null,
    })
  }

  return (
    <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-6 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 m-0">
            <Sparkles className="w-5 h-5 text-[#FF8900]" />
            Analyze Job Requirements
          </h2>
          <p className="text-sm text-[#b0abab] mt-1 m-0">
            Submit a public job posting URL or paste the job description to extract structured technical requirements.
          </p>
        </div>

        {/* Input Mode Selector */}
        <div className="inline-flex rounded-xl bg-[#2a2929] p-1 border border-[#3a3838]">
          <button
            type="button"
            disabled={isAnalyzing}
            onClick={() => { setInputMode('url'); setValidationError('') }}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer border-none ${
              inputMode === 'url'
                ? 'bg-[#FF8900] text-white shadow'
                : 'text-[#b0abab] hover:text-white bg-transparent'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            Posting URL
          </button>
          <button
            type="button"
            disabled={isAnalyzing}
            onClick={() => { setInputMode('paste'); setValidationError('') }}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer border-none ${
              inputMode === 'paste'
                ? 'bg-[#FF8900] text-white shadow'
                : 'text-[#b0abab] hover:text-white bg-transparent'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Paste Text
          </button>
        </div>
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

        {/* Dynamic Input: URL vs Pasted Description */}
        {inputMode === 'url' ? (
          <div>
            <label className="block text-xs font-medium text-[#d4cfcf] mb-1">
              Public Job Posting URL <span className="text-rose-400">*</span>
            </label>
            <div className="relative">
              <input
                type="url"
                disabled={isAnalyzing}
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                placeholder="https://boards.greenhouse.io/company/jobs/12345"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#232222] border border-[#3a3838] text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#FF8900] transition-colors"
              />
              <Globe className="w-4 h-4 text-[#888] absolute left-3.5 top-3" />
            </div>
            <p className="text-[11px] text-[#888] mt-1.5 m-0">
              Note: If the site blocks automated retrieval (login required, Cloudflare/CAPTCHA), switch to "Paste Text".
            </p>
          </div>
        ) : (
          <div>
            <label className="block text-xs font-medium text-[#d4cfcf] mb-1">
              Paste Full Job Description <span className="text-rose-400">*</span>
            </label>
            <textarea
              rows={7}
              disabled={isAnalyzing}
              value={pastedDescription}
              onChange={(e) => setPastedDescription(e.target.value)}
              placeholder="Paste the complete responsibilities, qualifications, and requirements from the job posting..."
              className="w-full p-3.5 rounded-xl bg-[#232222] border border-[#3a3838] text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#FF8900] transition-colors resize-y"
            />
            <div className="flex items-center justify-between text-[11px] text-[#888] mt-1">
              <span>Authoritative text source for extraction</span>
              <span>{pastedDescription.length} characters</span>
            </div>
          </div>
        )}

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
