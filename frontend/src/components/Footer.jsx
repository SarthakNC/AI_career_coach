/**
 * Footer — Shared site footer for public pages.
 */
import { Link } from 'react-router-dom'
import { Sparkles } from 'lucide-react'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-[#353333] bg-[#1a1919]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#FF8900] to-[#b35f00] p-0.5 flex items-center justify-center">
                <div className="w-full h-full bg-[#232222] rounded-[6px] flex items-center justify-center">
                  <Sparkles className="w-3.5 h-3.5 text-[#FF8900]" />
                </div>
              </div>
              <span className="text-base font-bold text-white">
                Parivartan <span className="text-[#FF8900]">AI</span>
              </span>
            </div>
            <p className="text-sm text-[#9c9797] leading-relaxed max-w-md">
              An evidence-based AI career coaching platform that compares your GitHub
              portfolio with real job requirements, delivering objective skill-gap analysis
              grounded in your actual code.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-3">Platform</h4>
            <ul className="space-y-2 list-none p-0 m-0">
              <li><Link to="/" className="text-sm text-[#9c9797] hover:text-[#FF8900] transition-colors no-underline">Home</Link></li>
              <li><Link to="/signup" className="text-sm text-[#9c9797] hover:text-[#FF8900] transition-colors no-underline">Get Started</Link></li>
              <li><Link to="/login" className="text-sm text-[#9c9797] hover:text-[#FF8900] transition-colors no-underline">Login</Link></li>
            </ul>
          </div>

          {/* Stack */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-3">Built With</h4>
            <ul className="space-y-2 list-none p-0 m-0">
              <li className="text-sm text-[#9c9797]">React + Vite</li>
              <li className="text-sm text-[#9c9797]">FastAPI + Python</li>
              <li className="text-sm text-[#9c9797]">Supabase PostgreSQL</li>
              <li className="text-sm text-[#9c9797]">Tailwind CSS</li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-[#2e2c2c] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#7d7878]">
          <p className="m-0">© {currentYear} Parivartan AI — Evidence-based AI Career Coach</p>
          <p className="m-0 text-[#FF8900]">FastAPI + React + Supabase</p>
        </div>
      </div>
    </footer>
  )
}
