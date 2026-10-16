/**
 * Navbar — Top navigation bar for public pages (Landing, Login, Signup).
 * Shows brand, section links, and auth CTAs.
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Sparkles, Menu, X } from 'lucide-react'

export default function Navbar() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const navLinks = [
    { label: 'Home', href: '#hero' },
    { label: 'Features', href: '#features' },
    { label: 'How It Works', href: '#how-it-works' },
    { label: 'About', href: '#benefits' },
  ]

  function scrollTo(href) {
    setMobileOpen(false)
    const el = document.querySelector(href)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' })
    }
  }

  function handleGetStarted() {
    if (user) {
      navigate('/dashboard')
    } else {
      navigate('/signup')
    }
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-[#353333] bg-[#1a1919]/90 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-2.5 no-underline" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#FF8900] to-[#b35f00] p-0.5 flex items-center justify-center shadow-lg shadow-[#FF8900]/20">
            <div className="w-full h-full bg-[#232222] rounded-[7px] flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-[#FF8900]" />
            </div>
          </div>
          <span className="text-lg font-bold text-white tracking-tight">
            CareerProof <span className="text-[#FF8900]">AI</span>
          </span>
        </Link>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <button
              key={link.label}
              onClick={() => scrollTo(link.href)}
              className="text-sm text-[#b0abab] hover:text-white transition-colors bg-transparent border-none cursor-pointer"
            >
              {link.label}
            </button>
          ))}
        </div>

        {/* Desktop auth buttons */}
        <div className="hidden md:flex items-center gap-3">
          {user ? (
            <button
              onClick={() => navigate('/dashboard')}
              className="text-sm font-medium px-4 py-2 rounded-lg bg-[#FF8900] hover:bg-[#e67a00] text-black transition-colors cursor-pointer border-none"
            >
              Dashboard
            </button>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm font-medium text-[#d4cfcf] hover:text-white transition-colors px-3 py-2 no-underline"
              >
                Login
              </Link>
              <button
                onClick={handleGetStarted}
                className="text-sm font-semibold px-4 py-2 rounded-lg bg-[#FF8900] hover:bg-[#e67a00] text-black transition-colors cursor-pointer border-none"
              >
                Get Started
              </button>
            </>
          )}
        </div>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden text-white bg-transparent border-none cursor-pointer"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-[#353333] bg-[#1a1919] px-4 pb-4 pt-2 space-y-2">
          {navLinks.map((link) => (
            <button
              key={link.label}
              onClick={() => scrollTo(link.href)}
              className="block w-full text-left text-sm text-[#b0abab] hover:text-white py-2 bg-transparent border-none cursor-pointer"
            >
              {link.label}
            </button>
          ))}
          <div className="pt-3 border-t border-[#353333] flex flex-col gap-2">
            {user ? (
              <button
                onClick={() => { setMobileOpen(false); navigate('/dashboard') }}
                className="text-sm font-medium px-4 py-2.5 rounded-lg bg-[#FF8900] hover:bg-[#e67a00] text-black transition-colors cursor-pointer border-none"
              >
                Dashboard
              </button>
            ) : (
              <>
                <Link
                  to="/login"
                  onClick={() => setMobileOpen(false)}
                  className="text-sm text-center text-[#d4cfcf] hover:text-white py-2 no-underline"
                >
                  Login
                </Link>
                <button
                  onClick={() => { setMobileOpen(false); handleGetStarted() }}
                  className="text-sm font-semibold px-4 py-2.5 rounded-lg bg-[#FF8900] hover:bg-[#e67a00] text-black transition-colors cursor-pointer border-none"
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
