import { useState, useRef } from 'react'
import {
  FileText,
  Sparkles,
  AlertCircle,
  Loader2,
  UploadCloud,
  FileCheck,
  X,
  AlertTriangle,
  ScanText,
  Layers,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { extractPdfJobDescription } from '../services/api'

export default function JobAnalysisForm({ onSubmit, isAnalyzing, currentStage }) {
  const { session } = useAuth()
  const token = session?.access_token

  // Mode: 'pdf' or 'paste'
  const [inputMode, setInputMode] = useState('pdf')

  // Common metadata
  const [jobTitle, setJobTitle] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [validationError, setValidationError] = useState('')

  // Paste mode state
  const [pastedDescription, setPastedDescription] = useState('')

  // PDF mode state
  const [selectedFile, setSelectedFile] = useState(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [isExtractingPdf, setIsExtractingPdf] = useState(false)
  const [extractionResult, setExtractionResult] = useState(null)
  const [pdfError, setPdfError] = useState('')
  const [confirmedPdfText, setConfirmedPdfText] = useState('')

  const fileInputRef = useRef(null)

  const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 // 10MB

  function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  function handleFileSelect(file) {
    setPdfError('')
    setValidationError('')

    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setPdfError('Invalid file type. Please select a valid PDF document (.pdf).')
      return
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setPdfError(`File size (${formatBytes(file.size)}) exceeds the 10 MB maximum upload limit.`)
      return
    }

    setSelectedFile(file)
    setExtractionResult(null)
    setConfirmedPdfText('')
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  function handleDragOver(e) {
    e.preventDefault()
    setIsDragOver(true)
  }

  function handleDragLeave(e) {
    e.preventDefault()
    setIsDragOver(false)
  }

  function resetPdfState() {
    setSelectedFile(null)
    setExtractionResult(null)
    setConfirmedPdfText('')
    setPdfError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  async function handleExtractPdf() {
    if (!selectedFile) {
      setPdfError('Please choose or drop a PDF document first.')
      return
    }

    setPdfError('')
    setIsExtractingPdf(true)

    try {
      const result = await extractPdfJobDescription(selectedFile, token)
      setExtractionResult(result)
      setConfirmedPdfText(result.extracted_text || '')

      // Auto-prefill detected metadata if not already filled by user
      if (result.detected_job_title && !jobTitle.trim()) {
        setJobTitle(result.detected_job_title)
      }
      if (result.detected_company_name && !companyName.trim()) {
        setCompanyName(result.detected_company_name)
      }
    } catch (err) {
      console.error('PDF extraction error:', err)
      setPdfError(err.message || 'Failed to extract text from the PDF document.')
    } finally {
      setIsExtractingPdf(false)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    setValidationError('')

    const textToSubmit = inputMode === 'pdf' ? confirmedPdfText : pastedDescription

    if (!textToSubmit || textToSubmit.trim().length < 50) {
      setValidationError(
        inputMode === 'pdf'
          ? 'The extracted job description must contain at least 50 characters before analysis.'
          : 'Please paste sufficient job description text (minimum 50 characters).'
      )
      return
    }

    onSubmit({
      pasted_description: textToSubmit.trim(),
      job_title: jobTitle.trim() || null,
      company_name: companyName.trim() || null,
      source_type: inputMode === 'pdf' ? 'pdf_upload' : 'pasted_text',
      extraction_method: extractionResult?.extraction_method || null,
    })
  }

  return (
    <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2 m-0">
          <Sparkles className="w-5 h-5 text-[#FF8900]" />
          Job Description Ingestion & Requirements
        </h2>
        <p className="text-sm text-[#b0abab] mt-1 m-0">
          Upload a digital or scanned PDF job posting, or paste text to extract verifiable skills.
        </p>
      </div>

      {/* Mode Selector Tabs */}
      <div className="flex items-center gap-2 border-b border-[#353333] pb-3 text-xs">
        <button
          type="button"
          onClick={() => {
            setInputMode('pdf')
            setValidationError('')
          }}
          className={`px-4 py-2 rounded-xl font-semibold transition-all flex items-center gap-2 cursor-pointer border ${
            inputMode === 'pdf'
              ? 'bg-[#FF8900]/15 text-[#FF8900] border-[#FF8900]/40 shadow-sm'
              : 'text-[#8c8888] hover:text-white bg-[#222121] border-[#333131]'
          }`}
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload PDF (Digital & OCR)</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setInputMode('paste')
            setValidationError('')
          }}
          className={`px-4 py-2 rounded-xl font-semibold transition-all flex items-center gap-2 cursor-pointer border ${
            inputMode === 'paste'
              ? 'bg-[#FF8900]/15 text-[#FF8900] border-[#FF8900]/40 shadow-sm'
              : 'text-[#8c8888] hover:text-white bg-[#222121] border-[#333131]'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Paste Raw Text</span>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Optional Metadata Row (Job Title & Company Name) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-[#d4cfcf] mb-1">
              Job Title <span className="text-[#888] font-normal">(optional)</span>
            </label>
            <input
              type="text"
              disabled={isAnalyzing || isExtractingPdf}
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
              disabled={isAnalyzing || isExtractingPdf}
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g. Stripe, Google, or Startup"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#232222] border border-[#3a3838] text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#FF8900] transition-colors"
            />
          </div>
        </div>

        {/* ─── TAB 1: PDF UPLOAD MODE ─── */}
        {inputMode === 'pdf' && (
          <div className="space-y-4">
            {/* If no text extracted yet, show the Drop Zone */}
            {!extractionResult ? (
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !selectedFile && fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
                  isDragOver
                    ? 'border-[#FF8900] bg-[#FF8900]/10 scale-[1.01]'
                    : 'border-[#383636] bg-[#1e1d1d] hover:border-[#4d4a4a]'
                } ${!selectedFile ? 'cursor-pointer' : ''}`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                  className="hidden"
                />

                {!selectedFile ? (
                  <div className="space-y-3">
                    <div className="w-12 h-12 rounded-full bg-[#2a2929] border border-[#3d3b3b] flex items-center justify-center mx-auto text-[#FF8900]">
                      <UploadCloud className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white m-0">
                        Drop your Job Description PDF here, or <span className="text-[#FF8900] underline">browse</span>
                      </p>
                      <p className="text-xs text-[#8c8888] mt-1 m-0">
                        Supports digital PDFs and scanned images via Tesseract OCR (up to 10 MB, 30 pages max).
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#262424] border border-[#3f3d3d] max-w-md mx-auto">
                      <div className="flex items-center gap-3 truncate text-left">
                        <FileCheck className="w-6 h-6 text-[#FF8900] shrink-0" />
                        <div className="truncate">
                          <p className="text-xs font-bold text-white truncate m-0">{selectedFile.name}</p>
                          <p className="text-[11px] text-[#8c8888] m-0">{formatBytes(selectedFile.size)}</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          resetPdfState()
                        }}
                        className="p-1 rounded-lg hover:bg-[#333] text-[#8c8888] hover:text-white transition-colors"
                        title="Remove file"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="flex justify-center gap-3">
                      <button
                        type="button"
                        onClick={handleExtractPdf}
                        disabled={isExtractingPdf}
                        className="px-6 py-2.5 rounded-xl bg-[#FF8900] hover:bg-[#e07900] disabled:opacity-50 text-white font-semibold text-xs transition-all shadow-md flex items-center gap-2 cursor-pointer border-none"
                      >
                        {isExtractingPdf ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Extracting & Running OCR...
                          </>
                        ) : (
                          <>
                            <ScanText className="w-4 h-4" />
                            Extract Text from PDF
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* When text has been successfully extracted, show Preview & Confirmation */
              <div className="space-y-4">
                {/* Extraction Meta Badge Bar */}
                <div className="p-4 rounded-xl bg-[#222121] border border-[#353333] flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-2 flex-wrap">
                    {extractionResult.extraction_method === 'text' && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Digital Text (Direct Extraction)
                      </span>
                    )}
                    {extractionResult.extraction_method === 'ocr' && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/15 text-purple-300 border border-purple-500/30">
                        <ScanText className="w-3.5 h-3.5" /> Full OCR Extraction (Scanned Pages)
                      </span>
                    )}
                    {extractionResult.extraction_method === 'mixed' && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                        <Layers className="w-3.5 h-3.5" /> Hybrid Digital + OCR
                      </span>
                    )}

                    <span className="text-[#8c8888] font-mono px-2 py-0.5 rounded bg-[#2c2a2a] border border-[#3d3b3b]">
                      {extractionResult.page_count} {extractionResult.page_count === 1 ? 'Page' : 'Pages'}
                    </span>

                    {extractionResult.ocr_pages && extractionResult.ocr_pages.length > 0 && (
                      <span className="text-[11px] text-purple-300">
                        (OCR applied on p. {extractionResult.ocr_pages.join(', ')})
                      </span>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={resetPdfState}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#2b2a2a] hover:bg-[#353333] text-[#d4cfcf] text-xs font-medium transition-colors border border-[#3a3838]"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Upload Different PDF
                  </button>
                </div>

                {/* Warnings Box if any */}
                {extractionResult.warnings && extractionResult.warnings.length > 0 && (
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs space-y-1">
                    <div className="flex items-center gap-1.5 font-semibold">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>Extraction Quality Notice</span>
                    </div>
                    <ul className="list-disc pl-5 space-y-0.5 text-amber-200/90 m-0">
                      {extractionResult.warnings.map((w, idx) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Editable Extracted Textarea */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-medium text-[#d4cfcf]">
                      Extracted Job Description Text <span className="text-[#888]">(Editable Preview)</span>
                    </label>
                    <span className="text-[11px] text-[#888]">
                      {confirmedPdfText.length} characters
                    </span>
                  </div>
                  <textarea
                    rows={10}
                    disabled={isAnalyzing}
                    value={confirmedPdfText}
                    onChange={(e) => setConfirmedPdfText(e.target.value)}
                    placeholder="Review and edit the extracted job requirements here before starting analysis..."
                    className="w-full p-3.5 rounded-xl bg-[#232222] border border-[#3a3838] text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#FF8900] transition-colors resize-y leading-relaxed"
                  />
                  <p className="text-[11px] text-[#888] mt-1 m-0">
                    Review and adjust any formatting, titles, or bullet points before confirming.
                  </p>
                </div>
              </div>
            )}

            {/* PDF Error Display */}
            {pdfError && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{pdfError}</span>
              </div>
            )}
          </div>
        )}

        {/* ─── TAB 2: PASTE TEXT MODE ─── */}
        {inputMode === 'paste' && (
          <div>
            <label className="block text-xs font-medium text-[#d4cfcf] mb-1">
              Job Description Text <span className="text-rose-400">*</span>
            </label>
            <textarea
              rows={8}
              disabled={isAnalyzing}
              value={pastedDescription}
              onChange={(e) => setPastedDescription(e.target.value)}
              placeholder="Paste the complete responsibilities, qualifications, and requirements from the job posting..."
              className="w-full p-3.5 rounded-xl bg-[#232222] border border-[#3a3838] text-white text-sm placeholder-[#666] focus:outline-none focus:border-[#FF8900] transition-colors resize-y leading-relaxed"
            />
            <div className="flex items-center justify-between text-[11px] text-[#888] mt-1">
              <span>Authoritative text source for requirement extraction</span>
              <span>{pastedDescription.length} characters (min 50)</span>
            </div>
          </div>
        )}

        {/* Form Validation Error Message */}
        {validationError && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{validationError}</span>
          </div>
        )}

        {/* Submit Action Area */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-[#2e2d2d]">
          <div className="text-xs text-[#9c9797]">
            {isAnalyzing && (
              <span className="flex items-center gap-2 text-[#FF8900] font-medium">
                <Loader2 className="w-4 h-4 animate-spin" />
                {currentStage || 'Processing requirement analysis...'}
              </span>
            )}
          </div>

          {/* Show submit button if in paste mode OR if PDF text is extracted and ready */}
          {(inputMode === 'paste' || (inputMode === 'pdf' && extractionResult)) && (
            <button
              type="submit"
              disabled={isAnalyzing || isExtractingPdf}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-[#FF8900] hover:bg-[#e07900] disabled:opacity-50 text-white font-semibold text-sm transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2 cursor-pointer border-none"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing Requirements...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  {inputMode === 'pdf' ? 'Confirm and Analyze Job Description' : 'Extract Requirements'}
                </>
              )}
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
