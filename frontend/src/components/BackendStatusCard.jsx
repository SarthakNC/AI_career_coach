import { Activity, AlertCircle, Clock, RefreshCw, Server } from 'lucide-react'

export default function BackendStatusCard({
  healthState,
  isRefreshing,
  onRetry,
  apiBaseUrl,
}) {
  const { status, data, error, latencyMs, timestamp } = healthState

  const isHealthy = status === 'healthy'
  const isFailed = status === 'error'
  const isLoading = status === 'loading' || isRefreshing

  return (
    <div className="rounded-2xl border border-[#3d3b3b] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6 shadow-xl relative overflow-hidden transition-all hover:border-[#524f4f]">
      {/* Decorative top accent glow */}
      <div
        className={`absolute top-0 left-0 right-0 h-1 ${
          isHealthy
            ? 'bg-emerald-500'
            : isFailed
            ? 'bg-rose-500'
            : 'bg-[#FF8900]'
        }`}
      />

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-[#1c1b1b] border border-[#383636]">
            <Server className="w-5 h-5 text-[#FF8900]" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white tracking-tight m-0">
              FastAPI Backend Service
            </h2>
            <p className="text-xs text-[#9c9797] font-mono mt-0.5">
              {apiBaseUrl}/health
            </p>
          </div>
        </div>

        {/* Retry Button */}
        <button
          onClick={onRetry}
          disabled={isLoading}
          id="btn-retry-health"
          className="flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-[#363434] hover:bg-[#444242] active:bg-[#2b2a2a] text-[#f0ecec] border border-[#484545] transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          title="Perform real health check against backend"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 text-[#FF8900] ${
              isLoading ? 'animate-spin' : ''
            }`}
          />
          <span>{isLoading ? 'Checking...' : 'Retry'}</span>
        </button>
      </div>

      {/* Main Status Display */}
      <div className="mt-5 pt-4 border-t border-[#383636]">
        {isLoading && (
          <div className="flex items-center space-x-3 py-2 text-amber-400">
            <RefreshCw className="w-5 h-5 animate-spin" />
            <div>
              <p className="text-sm font-semibold text-white">Checking backend connectivity...</p>
              <p className="text-xs text-[#9c9797]">Sending request to {apiBaseUrl}/health</p>
            </div>
          </div>
        )}

        {!isLoading && isHealthy && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2.5">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
              <span className="text-sm font-semibold text-emerald-400">
                Connected & Operational
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800 font-mono">
                HTTP 200
              </span>
            </div>

            <div className="bg-[#1c1b1b] rounded-xl p-3 border border-[#383636] text-xs font-mono text-[#d1cbcb]">
              <div className="flex justify-between items-center pb-1 mb-1 border-b border-[#2b2a2a]">
                <span className="text-[#888484]">Payload message:</span>
                <span className="text-emerald-300 font-medium">{data?.message}</span>
              </div>
              <div className="flex justify-between items-center pt-0.5">
                <span className="text-[#888484]">Backend status:</span>
                <span className="text-white">{data?.status}</span>
              </div>
            </div>
          </div>
        )}

        {!isLoading && isFailed && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-rose-400">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-semibold">Backend Unavailable</span>
            </div>

            <div className="bg-[#241717] rounded-xl p-3 border border-rose-900/40 text-xs text-rose-200">
              <p className="font-medium">{error?.message || 'Connection refused'}</p>
              <p className="text-[11px] text-[#a89292] mt-1 font-mono">
                Verify FastAPI is running on port 8000 via Uvicorn.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Meta Footer */}
      <div className="mt-4 pt-3 border-t border-[#333131] flex items-center justify-between text-[11px] text-[#858080]">
        <div className="flex items-center space-x-1.5">
          <Activity className="w-3.5 h-3.5 text-[#FF8900]" />
          <span>Latency: {latencyMs !== null ? `${latencyMs} ms` : '--'}</span>
        </div>
        <div className="flex items-center space-x-1">
          <Clock className="w-3.5 h-3.5" />
          <span>Last checked: {timestamp || 'Never'}</span>
        </div>
      </div>
    </div>
  )
}
