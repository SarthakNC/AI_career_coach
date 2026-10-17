import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import {
  getAssessmentOptions,
  createAssessment,
  getAssessmentById
} from '../services/api'
import AssessmentSetup from '../components/AssessmentSetup'
import AssessmentScoreOverview from '../components/AssessmentScoreOverview'
import RequirementResultsTable from '../components/RequirementResultsTable'
import PrioritizedGapsSection from '../components/PrioritizedGapsSection'
import ActionableRecommendationsSection from '../components/ActionableRecommendationsSection'
import AssessmentVersionModal from '../components/AssessmentVersionModal'
import {
  BarChart3,
  Sparkles,
  History,
  Target,
  FileText,
  Layers,
  ArrowLeft,
  Loader2,
  AlertCircle
} from 'lucide-react'

export default function SkillGapAssessmentPage() {
  const { session } = useAuth()
  const token = session?.access_token

  // Navigation tab: 'new' | 'current'
  const [activeTab, setActiveTab] = useState('new')
  // Detail sub-view in 'current' assessment: 'requirements' | 'gaps' | 'recommendations'
  const [activeView, setActiveView] = useState('requirements')

  const [options, setOptions] = useState({ jobs: [], repositories: [] })
  const [activeAssessment, setActiveAssessment] = useState(null)
  const [showVersionModal, setShowVersionModal] = useState(false)

  const [loadingOptions, setLoadingOptions] = useState(true)
  const [loadingAssessment, setLoadingAssessment] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  // Load initial options when token is present
  useEffect(() => {
    if (token) {
      loadInitialData()
    }
  }, [token])

  async function loadInitialData() {
    try {
      setLoadingOptions(true)
      setErrorMessage('')

      try {
        const optData = await getAssessmentOptions(token)
        setOptions(optData || { jobs: [], repositories: [] })
      } catch (optErr) {
        console.error('Failed to load assessment options:', optErr)
        setErrorMessage(optErr.message || 'Failed to load jobs or repositories.')
      }
    } finally {
      setLoadingOptions(false)
    }
  }

  // Handle starting a new assessment
  async function handleStartAssessment({ jobId, repositoryIds }) {
    try {
      setGenerating(true)
      setErrorMessage('')
      const created = await createAssessment({ jobId, repositoryIds }, token)
      setActiveAssessment(created)
      setActiveTab('current')
      setActiveView('requirements')
    } catch (err) {
      console.error('Assessment generation error:', err)
      setErrorMessage(err.message || 'Failed to execute skill gap assessment.')
    } finally {
      setGenerating(false)
    }
  }

  // Open an assessment version
  async function handleSelectAssessment(id) {
    try {
      setLoadingAssessment(true)
      setErrorMessage('')
      const fullData = await getAssessmentById(id, token)
      setActiveAssessment(fullData)
      setActiveTab('current')
      setActiveView('requirements')
    } catch (err) {
      console.error('Failed to load assessment detail:', err)
      setErrorMessage(err.message || 'Failed to retrieve assessment details.')
    } finally {
      setLoadingAssessment(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Title & Navigation Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#353333] pb-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-[#FF8900]" />
            AI Skill-Gap Assessment
          </h1>
          <p className="text-xs text-[#8c8888] mt-1">
            Ground job expectations in verified GitHub repository evidence with deterministic scoring.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#1a1919] border border-[#353333] text-xs">
          <button
            onClick={() => setActiveTab('new')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-colors ${
              activeTab === 'new'
                ? 'bg-[#FF8900] text-black font-semibold'
                : 'text-[#8c8888] hover:text-white hover:bg-[#2e2d2d]'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>New Assessment</span>
          </button>

          {activeAssessment && (
            <button
              onClick={() => setActiveTab('current')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-colors ${
                activeTab === 'current'
                  ? 'bg-[#FF8900] text-black font-semibold'
                  : 'text-[#8c8888] hover:text-white hover:bg-[#2e2d2d]'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Current Results</span>
            </button>
          )}
        </div>
      </div>

      {/* Global Error Banner */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage('')}
            className="text-xs text-rose-400 hover:text-rose-200 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tab: New Assessment */}
      {activeTab === 'new' && (
        loadingOptions ? (
          <div className="p-16 text-center rounded-2xl bg-[#1f1e1e] border border-[#353333] space-y-3">
            <Loader2 className="w-7 h-7 animate-spin text-[#FF8900] mx-auto" />
            <p className="text-xs text-[#8c8888]">Loading analyzed jobs and repository portfolio...</p>
          </div>
        ) : (
          <AssessmentSetup
            jobs={options.jobs}
            repositories={options.repositories}
            onStartAssessment={handleStartAssessment}
            loading={generating}
            error={errorMessage}
          />
        )
      )}

      {/* Tab: Current Results */}
      {activeTab === 'current' && (
        loadingAssessment ? (
          <div className="p-16 text-center rounded-2xl bg-[#1f1e1e] border border-[#353333] space-y-3">
            <Loader2 className="w-7 h-7 animate-spin text-[#FF8900] mx-auto" />
            <p className="text-xs text-[#8c8888]">Retrieving persisted assessment snapshot...</p>
          </div>
        ) : activeAssessment ? (
          <div className="space-y-6">
            {/* Top Toolbar */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setActiveTab('new')}
                  className="flex items-center gap-1.5 text-xs text-[#8c8888] hover:text-white transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Start another assessment</span>
                </button>
                <button
                  onClick={() => setShowVersionModal(true)}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#252424] hover:bg-[#333131] border border-[#3d3b3b] text-xs text-amber-300 font-medium transition-colors"
                >
                  <History className="w-3.5 h-3.5 text-amber-400" />
                  <span>Version Lineage (v{activeAssessment.version || 1})</span>
                </button>
              </div>

              {/* Sub-view switcher */}
              <div className="flex items-center gap-1 p-1 rounded-lg bg-[#1a1919] border border-[#353333] text-xs">
                <button
                  onClick={() => setActiveView('requirements')}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-md font-medium transition-colors ${
                    activeView === 'requirements'
                      ? 'bg-[#333131] text-white'
                      : 'text-[#8c8888] hover:text-white'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 text-[#FF8900]" />
                  <span>Requirements ({activeAssessment.requirement_results?.length || 0})</span>
                </button>

                <button
                  onClick={() => setActiveView('gaps')}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-md font-medium transition-colors ${
                    activeView === 'gaps'
                      ? 'bg-[#333131] text-white'
                      : 'text-[#8c8888] hover:text-white'
                  }`}
                >
                  <Target className="w-3.5 h-3.5 text-rose-400" />
                  <span>Prioritized Gaps ({activeAssessment.prioritized_gaps?.length || 0})</span>
                </button>

                <button
                  onClick={() => setActiveView('recommendations')}
                  className={`flex items-center gap-1.5 px-3 py-1 rounded-md font-medium transition-colors ${
                    activeView === 'recommendations'
                      ? 'bg-[#333131] text-white'
                      : 'text-[#8c8888] hover:text-white'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Action Plan ({activeAssessment.recommendations?.length || 0})</span>
                </button>
              </div>
            </div>

            {/* Score Overview Banner */}
            <AssessmentScoreOverview assessment={activeAssessment} />

            {/* Sub-view Content */}
            {activeView === 'requirements' && (
              <RequirementResultsTable results={activeAssessment.requirement_results || []} />
            )}

            {activeView === 'gaps' && (
              <PrioritizedGapsSection gaps={activeAssessment.prioritized_gaps || []} />
            )}

            {activeView === 'recommendations' && (
              <ActionableRecommendationsSection recommendations={activeAssessment.recommendations || []} />
            )}

            {/* Assessment Version Lineage Modal */}
            {showVersionModal && activeAssessment && (
              <AssessmentVersionModal
                assessmentId={activeAssessment.id}
                token={token}
                onClose={() => setShowVersionModal(false)}
                onSelectVersion={async (verId) => {
                  setShowVersionModal(false)
                  await handleSelectAssessment(verId)
                }}
              />
            )}
          </div>
        ) : (
          <div className="p-12 text-center rounded-2xl bg-[#1f1e1e] border border-dashed border-[#353333] space-y-3">
            <p className="text-xs text-[#8c8888]">No active assessment selected.</p>
            <button
              onClick={() => setActiveTab('new')}
              className="px-4 py-2 rounded-lg bg-[#FF8900] text-black text-xs font-bold"
            >
              Start New Assessment
            </button>
          </div>
        )
      )}
    </div>
  )
}
