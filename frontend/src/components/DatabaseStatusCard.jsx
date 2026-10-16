import { AlertTriangle, CheckCircle2, Database, HelpCircle, ShieldCheck } from 'lucide-react'

export default function DatabaseStatusCard({ systemStatus }) {
  const db = systemStatus?.database || {
    status: 'not_configured',
    configured: false,
    message: 'Configuration pending until verified.',
  }

  const isConnected = db.status === 'connected'
  const isNotConfigured = db.status === 'not_configured' || !db.configured
  const isError = db.status === 'error' && db.configured

  return (
    <div className="rounded-2xl border border-[#3d3b3b] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6 shadow-xl relative overflow-hidden transition-all hover:border-[#524f4f]">
      {/* Decorative top accent glow */}
      <div
        className={`absolute top-0 left-0 right-0 h-1 ${
          isConnected
            ? 'bg-emerald-500'
            : isError
            ? 'bg-rose-500'
            : 'bg-amber-500'
        }`}
      />

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-[#1c1b1b] border border-[#383636]">
            <Database className="w-5 h-5 text-[#FF8900]" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white tracking-tight m-0">
              Supabase PostgreSQL
            </h2>
            <p className="text-xs text-[#9c9797] mt-0.5">
              Client Factory & Health Verification
            </p>
          </div>
        </div>

        {/* State Badge */}
        <div>
          {isConnected && (
            <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950/70 text-emerald-300 border border-emerald-800">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Connected</span>
            </span>
          )}

          {isNotConfigured && (
            <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-950/70 text-amber-300 border border-amber-800">
              <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
              <span>Pending Configuration</span>
            </span>
          )}

          {isError && (
            <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-950/70 text-rose-300 border border-rose-800">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              <span>Connection Error</span>
            </span>
          )}
        </div>
      </div>

      {/* Main Status Body */}
      <div className="mt-5 pt-4 border-t border-[#383636] space-y-3">
        <div className="bg-[#1c1b1b] rounded-xl p-3.5 border border-[#383636]">
          <div className="flex items-start space-x-2.5">
            <div className="mt-0.5">
              {isNotConfigured ? (
                <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              ) : isConnected ? (
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
              ) : (
                <div className="w-2 h-2 rounded-full bg-rose-400" />
              )}
            </div>
            <div className="flex-1 text-xs">
              <p className="font-semibold text-white">
                {isNotConfigured
                  ? 'Configuration Pending Verification'
                  : isConnected
                  ? 'Database Live & Authenticated'
                  : 'Database Handshake Failed'}
              </p>
              <p className="text-[#a39e9e] mt-1 leading-relaxed">
                {db.message}
              </p>
            </div>
          </div>
        </div>

        <div className="text-xs text-[#8c8787] space-y-1.5 px-1">
          <div className="flex items-center justify-between">
            <span>Environment variables:</span>
            <span className="font-mono text-[11px] text-[#cfcaca]">
              SUPABASE_URL, SUPABASE_KEY
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Phase 1 schema migration:</span>
            <span className="text-[#a8a4a4]">Deferred to Phase 2 (by design)</span>
          </div>
        </div>
      </div>

      {/* Footer / Security Guarantee */}
      <div className="mt-4 pt-3 border-t border-[#333131] flex items-center justify-between text-[11px] text-[#858080]">
        <div className="flex items-center space-x-1 text-emerald-400/90">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Zero Client-side Secret Exposure</span>
        </div>
        <span className="font-mono text-[10px] text-[#6b6666]">backend/database.py</span>
      </div>
    </div>
  )
}
