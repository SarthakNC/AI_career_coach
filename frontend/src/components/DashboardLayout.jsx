/**
 * DashboardLayout — Sidebar + top-bar + content layout for authenticated pages.
 */
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  Activity,
  BarChart3,
  BookOpen,
  ChevronLeft,
  GitBranch,
  Home,
  Layers,
  LogOut,
  Menu,
  Settings,
  Sparkles,
  User,
} from 'lucide-react'

const sidebarLinks = [
  { to: '/dashboard', icon: Home, label: 'Dashboard', end: true },
  { to: '/dashboard/jobs', icon: BookOpen, label: 'Job Analysis' },
  { to: '/dashboard/github', icon: GitBranch, label: 'GitHub Portfolio' },
  { to: '/dashboard/activity', icon: Activity, label: 'Repository Activity' },
  { to: '/dashboard/skills', icon: BarChart3, label: 'Skill Gaps' },
  { to: '/dashboard/settings', icon: Settings, label: 'Settings' },
]

export default function DashboardLayout() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)

  const displayName =
    user?.user_metadata?.full_name ||
    user?.email?.split('@')[0] ||
    'User'

  async function handleLogout() {
    await signOut()
    navigate('/', { replace: true })
  }

  const linkClasses = ({ isActive }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-[#FF8900]/10 text-[#FF8900] border border-[#FF8900]/25'
        : 'text-[#b0abab] hover:bg-[#333131] hover:text-white border border-transparent'
    }`

  return (
    <div className="min-h-screen bg-[#232222] flex">
      {/* ─── SIDEBAR (Desktop) ─── */}
      <aside className="hidden lg:flex flex-col w-64 border-r border-[#353333] bg-[#1a1919] fixed inset-y-0 left-0 z-40">
        {/* Brand */}
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-[#353333]">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#FF8900] to-[#b35f00] p-0.5 flex items-center justify-center">
            <div className="w-full h-full bg-[#1a1919] rounded-[6px] flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-[#FF8900]" />
            </div>
          </div>
          <span className="text-base font-bold text-white">
            Parivartan <span className="text-[#FF8900]">AI</span>
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {sidebarLinks.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} className={linkClasses}>
              <link.icon className="w-4 h-4 flex-shrink-0" />
              <span>{link.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="px-3 py-4 border-t border-[#353333]">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors bg-transparent border-none cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* ─── MOBILE SIDEBAR OVERLAY ─── */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-black/60"
            onClick={() => setSidebarOpen(false)}
          />
          <aside className="relative flex flex-col w-64 bg-[#1a1919] border-r border-[#353333] z-50">
            <div className="h-16 flex items-center justify-between px-5 border-b border-[#353333]">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#FF8900]" />
                <span className="text-base font-bold text-white">
                  Parivartan <span className="text-[#FF8900]">AI</span>
                </span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="text-[#b0abab] hover:text-white bg-transparent border-none cursor-pointer"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
            </div>
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
              {sidebarLinks.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  end={link.end}
                  className={linkClasses}
                  onClick={() => setSidebarOpen(false)}
                >
                  <link.icon className="w-4 h-4 flex-shrink-0" />
                  <span>{link.label}</span>
                </NavLink>
              ))}
            </nav>
            <div className="px-3 py-4 border-t border-[#353333]">
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-rose-400 hover:bg-rose-500/10 transition-colors bg-transparent border-none cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </aside>
        </div>
      )}

      {/* ─── MAIN CONTENT AREA ─── */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-16 border-b border-[#353333] bg-[#1a1919]/90 backdrop-blur-xl flex items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              className="lg:hidden text-[#b0abab] hover:text-white bg-transparent border-none cursor-pointer"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-5 h-5" />
            </button>
            <p className="text-sm text-[#d4cfcf] m-0">
              Welcome, <span className="font-semibold text-white">{displayName}</span>
            </p>
          </div>

          {/* Profile dropdown */}
          <div className="relative">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#2a2929] hover:bg-[#333131] border border-[#3a3838] text-sm text-white transition-colors cursor-pointer"
            >
              <div className="w-7 h-7 rounded-full bg-[#FF8900]/20 border border-[#FF8900]/30 flex items-center justify-center">
                <User className="w-3.5 h-3.5 text-[#FF8900]" />
              </div>
              <span className="hidden sm:inline text-[#d4cfcf]">{displayName}</span>
            </button>

            {profileOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setProfileOpen(false)} />
                <div className="absolute right-0 mt-2 w-56 rounded-xl border border-[#3a3838] bg-[#2a2929] shadow-xl z-50 py-2">
                  <div className="px-4 py-2 border-b border-[#353333]">
                    <p className="text-sm font-medium text-white m-0">{displayName}</p>
                    <p className="text-xs text-[#9c9797] mt-0.5 m-0 truncate">{user?.email}</p>
                  </div>
                  <button
                    onClick={() => { setProfileOpen(false); handleLogout() }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-rose-400 hover:bg-rose-500/10 transition-colors bg-transparent border-none cursor-pointer"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              </>
            )}
          </div>
        </header>

        {/* Page content outlet */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
