import { Cpu, ExternalLink, ShieldCheck, Sparkles } from 'lucide-react'

export default function Header({ apiBaseUrl }) {
  return (
    <header className="border-b border-[#353333] bg-[#1a1919]/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF8900] to-[#b35f00] p-0.5 flex items-center justify-center shadow-lg shadow-[#FF8900]/20">
            <div className="w-full h-full bg-[#232222] rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-[#FF8900]" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white m-0">
                Parivartan <span className="text-[#FF8900]">AI</span>
              </h1>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-[#FF8900]/15 text-[#FF8900] border border-[#FF8900]/30 tracking-wider">
                AI Platform
              </span>
            </div>
            <p className="text-xs text-[#9e9a9a] m-0 font-medium tracking-wide">
              Evidence-based AI Career Coach
            </p>
          </div>
        </div>

        {/* Header Actions / Meta */}
        <div className="flex items-center space-x-3">
          <div className="hidden md:flex items-center space-x-2 text-xs text-[#b0abab] bg-[#2a2929] px-3 py-1.5 rounded-lg border border-[#3d3b3b]">
            <ShieldCheck className="w-3.5 h-3.5 text-[#FF8900]" />
            <span>Secure Architecture</span>
          </div>
          <a
            href={`${apiBaseUrl}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 text-xs font-medium text-white bg-[#2e2d2d] hover:bg-[#383737] px-3 py-2 rounded-lg border border-[#444242] transition-colors"
            title="Open FastAPI Swagger Interactive Documentation"
          >
            <Cpu className="w-3.5 h-3.5 text-[#FF8900]" />
            <span>API Docs</span>
            <ExternalLink className="w-3 h-3 text-[#9e9a9a]" />
          </a>
        </div>
      </div>
    </header>
  )
}
