import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { analyzeJob, listSavedJobs, getJobDetails, deleteSavedJob } from '../services/api'
import JobAnalysisForm from '../components/JobAnalysisForm'
import RequirementList from '../components/RequirementList'
import JobHistory from '../components/JobHistory'
import { AlertCircle, Loader2, Sparkles, PlusCircle } from 'lucide-react'

// UI Analysis Stages
const STAGES = {
  IDLE: 'idle',
  VALIDATING: 'validating',
  RETRIEVING: 'retrieving',
  ANALYZING: 'analyzing',
  SAVING: 'saving',
  SUCCESS: 'success',
  ERROR: 'error',
}

const STAGE_LABELS = {
  [STAGES.VALIDATING]: 'Validating inputs and security checks...',
  [STAGES.RETRIEVING]: 'Retrieving public job posting content...',
  [STAGES.ANALYZING]: 'Extracting requirements with LLM reasoning...',
  [STAGES.SAVING]: 'Saving structured skills to Supabase database...',
}

export default function JobAnalysisPage() {
  const { session } = useAuth()
  const token = session?.access_token

  const [savedJobs, setSavedJobs] = useState([])
  const [activeJob, setActiveJob] = useState(null)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [stage, setStage] = useState(STAGES.IDLE)
  const [errorMessage, setErrorMessage] = useState('')
  const [showForm, setShowForm] = useState(true)

  // Fetch initial history
  useEffect(() => {
    if (token) {
      loadHistory()
    }
  }, [token])

  async function loadHistory() {
    try {
      setLoadingHistory(true)
      const data = await listSavedJobs(token)
      setSavedJobs(data || [])
      // If no active job is selected and jobs exist, load the most recent one
      if (!activeJob && data && data.length > 0) {
        handleSelectJob(data[0].id)
      }
    } catch (err) {
      console.error('Error fetching jobs history:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  async function handleSelectJob(jobId) {
    try {
      const fullJob = await getJobDetails(jobId, token)
      setActiveJob(fullJob)
      setShowForm(false)
      setErrorMessage('')
    } catch (err) {
      setErrorMessage(err.message || 'Failed to load job details.')
    }
  }

  async function handleDeleteJob(jobId) {
    try {
      await deleteSavedJob(jobId, token)
      setSavedJobs((prev) => prev.filter((j) => j.id !== jobId))
      if (activeJob?.id === jobId) {
        setActiveJob(null)
        setShowForm(true)
      }
    } catch (err) {
      setErrorMessage(err.message || 'Failed to delete job analysis.')
    }
  }

  async function handleFormSubmit(formData) {
    setErrorMessage('')
    setStage(STAGES.VALIDATING)

    try {
      // Step: Validating
      await new Promise((r) => setTimeout(r, 400))

      setStage(STAGES.ANALYZING)
      const result = await analyzeJob(formData, token)

      setStage(STAGES.SAVING)
      await new Promise((r) => setTimeout(r, 300))

      setStage(STAGES.SUCCESS)
      setActiveJob(result)
      setShowForm(false)

      // Refresh history
      loadHistory()
    } catch (err) {
      setStage(STAGES.ERROR)
      setErrorMessage(err.message || 'An unexpected error occurred during job analysis.')
    }
  }

  const isAnalyzing = [
    STAGES.VALIDATING,
    STAGES.RETRIEVING,
    STAGES.ANALYZING,
    STAGES.SAVING,
  ].includes(stage)

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-[#353333]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-3 m-0">
            <span className="p-2 rounded-xl bg-gradient-to-br from-[#FF8900] to-[#b35f00] text-white">
              <Sparkles className="w-5 h-5" />
            </span>
            Job Requirement Analyzer
          </h1>
          <p className="text-sm text-[#b0abab] mt-1 m-0">
            Extract evidence-based skills and technical qualifications from real job postings.
          </p>
        </div>

        <button
          onClick={() => { setShowForm(true); setErrorMessage('') }}
          className="self-start sm:self-auto px-4 py-2.5 rounded-xl bg-[#2a2929] hover:bg-[#333131] border border-[#3a3838] text-sm font-semibold text-white transition-all flex items-center gap-2 cursor-pointer"
        >
          <PlusCircle className="w-4 h-4 text-[#FF8900]" />
          New Job Analysis
        </button>
      </div>

      {/* Global Error Banner */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold m-0 mb-0.5">Analysis Error</p>
            <p className="text-xs text-rose-200 m-0">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Main Grid: Left = Form / Results, Right = History Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {showForm ? (
            <JobAnalysisForm
              onSubmit={handleFormSubmit}
              isAnalyzing={isAnalyzing}
              currentStage={STAGE_LABELS[stage]}
            />
          ) : (
            <RequirementList
              job={activeJob}
              onNewAnalysis={() => { setShowForm(true); setErrorMessage('') }}
            />
          )}
        </div>

        {/* Right Column (1 col): Saved Analyses History */}
        <div className="space-y-6">
          {loadingHistory ? (
            <div className="bg-[#1a1919] border border-[#353333] rounded-2xl p-6 text-center">
              <Loader2 className="w-6 h-6 animate-spin text-[#FF8900] mx-auto mb-2" />
              <p className="text-xs text-[#888] m-0">Loading saved analyses...</p>
            </div>
          ) : (
            <JobHistory
              jobs={savedJobs}
              activeJobId={activeJob?.id}
              onSelectJob={handleSelectJob}
              onDeleteJob={handleDeleteJob}
            />
          )}
        </div>
      </div>
    </div>
  )
}
