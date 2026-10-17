import { useEffect, useState, useCallback } from 'react'
import BackendStatusCard from '../components/BackendStatusCard'
import DatabaseStatusCard from '../components/DatabaseStatusCard'
import ProjectDescriptionCard from '../components/ProjectDescriptionCard'
import SkillGapPreviewSection from '../components/SkillGapPreviewSection'
import { checkBackendHealth, getSystemStatus, API_BASE_URL } from '../services/api'

export default function Dashboard() {
  const [healthState, setHealthState] = useState({
    status: 'loading',
    data: null,
    error: null,
    latencyMs: null,
    timestamp: null,
  })

  const [systemStatus, setSystemStatus] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const performFetch = useCallback(async () => {
    try {
      const [healthData, statusData] = await Promise.all([
        checkBackendHealth(),
        getSystemStatus(),
      ])

      setHealthState({
        status: 'healthy',
        data: healthData,
        error: null,
        latencyMs: healthData.latencyMs,
        timestamp: healthData.timestamp,
      })
      setSystemStatus(statusData)
    } catch (err) {
      setHealthState({
        status: 'error',
        data: null,
        error: err,
        latencyMs: err.latencyMs ?? null,
        timestamp: err.timestamp || new Date().toLocaleTimeString(),
      })

      try {
        const fallbackStatus = await getSystemStatus()
        setSystemStatus(fallbackStatus)
      } catch {
        setSystemStatus({
          app_name: 'Parivartan AI API',
          version: '1.0.0',
          environment: 'development',
          database: {
            status: 'error',
            configured: false,
            message: 'Unable to query backend status endpoint.',
          },
        })
      }
    }
  }, [])

  useEffect(() => {
    let active = true

    async function initialize() {
      await performFetch()
    }

    if (active) {
      initialize()
    }

    return () => {
      active = false
    }
  }, [performFetch])

  const handleRetry = async () => {
    setIsRefreshing(true)
    await performFetch()
    setIsRefreshing(false)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 flex-1 w-full">
      {/* Real-Time Connectivity Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[#9c9797] m-0">
              System Infrastructure & Connectivity
            </h2>
            <p className="text-xs text-[#736e6e] mt-0.5">
              Live status validated via FastAPI and Supabase SDK
            </p>
          </div>
          <span className="text-[11px] font-mono text-[#a8a3a3] bg-[#272626] px-2.5 py-1 rounded-md border border-[#383636]">
            API: {API_BASE_URL}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <BackendStatusCard
            healthState={healthState}
            isRefreshing={isRefreshing}
            onRetry={handleRetry}
            apiBaseUrl={API_BASE_URL}
          />

          <DatabaseStatusCard
            systemStatus={systemStatus}
          />
        </div>
      </div>

      {/* Project Objective and Evidence Model */}
      <ProjectDescriptionCard />

      {/* Future Roadmap & Placeholder Skill Gap Section */}
      <SkillGapPreviewSection />
    </div>
  )
}
