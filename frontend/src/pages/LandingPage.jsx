/**
 * LandingPage — Public marketing page for Parivartan AI.
 * Sections: Hero, Features, How It Works, Benefits, CTA.
 */
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import FeatureCard from '../components/FeatureCard'
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  CheckCircle2,
  Code2,
  Eye,
  FileSearch,
  GitBranch,
  Layers,
  RefreshCw,
  Sparkles,
  Target,
  TrendingUp,
  Zap,
} from 'lucide-react'

export default function LandingPage() {
  const navigate = useNavigate()
  const { user } = useAuth()

  function handleGetStarted() {
    if (user) {
      navigate('/dashboard')
    } else {
      navigate('/signup')
    }
  }

  const features = [
    {
      icon: BookOpen,
      title: 'Job Requirement Analysis',
      description:
        'Parse real job postings to extract structured technical competencies, required seniority levels, and framework expectations.',
      badge: 'AI-Powered',
    },
    {
      icon: GitBranch,
      title: 'GitHub Portfolio Analysis',
      description:
        'Analyze your repositories for commit patterns, language depth, test coverage, and architectural decisions that demonstrate real skills.',
      badge: 'Evidence',
    },
    {
      icon: BarChart3,
      title: 'Evidence-Based Skill Gaps',
      description:
        'Calculate the objective delta between your proven portfolio evidence and employer requirements — no fabricated scores.',
      badge: 'Objective',
    },
    {
      icon: RefreshCw,
      title: 'Automatic Repository Reassessment',
      description:
        'As you improve your code and push updates, your skill-gap analysis refreshes automatically to reflect genuine progress.',
      badge: 'Live',
    },
  ]

  const steps = [
    {
      number: '01',
      icon: FileSearch,
      title: 'Select a real job or internship',
      description: 'Paste a job posting URL or enter the requirements you want to target.',
    },
    {
      number: '02',
      icon: Code2,
      title: 'Connect your GitHub portfolio',
      description: 'Enter your GitHub username so the platform can inspect your public repositories.',
    },
    {
      number: '03',
      icon: Target,
      title: 'Analyze evidence vs. requirements',
      description: 'AI compares your proven code skills against the job\'s technical expectations.',
    },
    {
      number: '04',
      icon: TrendingUp,
      title: 'Improve and reassess automatically',
      description: 'Push code updates and your assessment refreshes to show real, measurable progress.',
    },
  ]

  const benefits = [
    {
      icon: Eye,
      title: 'Understand what your portfolio actually proves',
      description: 'See exactly which technical competencies your GitHub repositories demonstrate, backed by commit history and code analysis.',
    },
    {
      icon: Layers,
      title: 'Identify missing evidence',
      description: 'Discover skill gaps where your repos lack the patterns, tests, or architectures that employers look for.',
    },
    {
      icon: Zap,
      title: 'Track improvements as your code evolves',
      description: 'As you build new projects and push updates, your skill profile updates automatically — showing genuine growth.',
    },
  ]

  return (
    <div className="min-h-screen bg-[#232222] text-[#e0e0e0] flex flex-col">
      <Navbar />

      {/* ─── HERO ─── */}
      <section id="hero" className="relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-[#FF8900]/[0.04] rounded-full blur-[120px]" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24 lg:pt-28 lg:pb-32">
          <div className="max-w-3xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FF8900]/10 border border-[#FF8900]/25 text-[#FF8900] text-xs font-semibold tracking-wider uppercase mb-6">
              <Sparkles className="w-3.5 h-3.5" />
              Evidence-Based Career Intelligence
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-[1.1] mb-6">
              Your GitHub Portfolio.{' '}
              <span className="bg-gradient-to-r from-[#FF8900] to-[#ffab42] bg-clip-text text-transparent">
                Your Career Proof.
              </span>
            </h1>

            <p className="text-lg sm:text-xl text-[#a8a3a3] leading-relaxed max-w-2xl mx-auto mb-10">
              Parivartan AI compares your demonstrated coding skills with real job
              requirements, replacing guesswork with objective, evidence-based career coaching.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={handleGetStarted}
                className="group flex items-center gap-2 px-7 py-3 rounded-xl bg-[#FF8900] hover:bg-[#e67a00] text-black font-semibold text-base transition-all shadow-lg shadow-[#FF8900]/20 hover:shadow-[#FF8900]/30 cursor-pointer border-none"
              >
                Get Started
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </button>
              <button
                onClick={() => {
                  const el = document.querySelector('#features')
                  if (el) el.scrollIntoView({ behavior: 'smooth' })
                }}
                className="flex items-center gap-2 px-7 py-3 rounded-xl bg-transparent border border-[#4a4848] hover:border-[#FF8900]/50 text-white font-medium text-base transition-all cursor-pointer"
              >
                Explore Features
              </button>
            </div>
          </div>

          {/* Dashboard Preview Panel */}
          <div className="mt-16 max-w-4xl mx-auto">
            <div className="rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#1e1d1d] p-1 shadow-2xl shadow-black/40">
              <div className="rounded-xl border border-[#333131] bg-[#232222] p-6 sm:p-8">
                {/* Mock top bar */}
                <div className="flex items-center gap-2 mb-6">
                  <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
                  <div className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
                  <div className="w-3 h-3 rounded-full bg-[#28ca42]" />
                  <span className="ml-3 text-xs text-[#7d7878] font-mono">parivartan-ai — skill-gap-analysis</span>
                </div>

                {/* Simulated skill-gap panel */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {[
                    { label: 'Job Requirements Parsed', value: 'React, Node.js, PostgreSQL, Docker…', color: '#FF8900' },
                    { label: 'Portfolio Evidence Found', value: 'Commit patterns, test suites, API design…', color: '#22c55e' },
                    { label: 'Skill Gap Identified', value: 'Docker deployment, CI/CD pipelines…', color: '#ef4444' },
                  ].map((item) => (
                    <div key={item.label} className="rounded-xl bg-[#1c1b1b] border border-[#383636] p-4">
                      <p className="text-[11px] uppercase tracking-wider font-semibold mb-2" style={{ color: item.color }}>
                        {item.label}
                      </p>
                      <p className="text-sm text-[#d1cbcb] leading-relaxed">{item.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── FEATURES ─── */}
      <section id="features" className="py-20 lg:py-24 border-t border-[#2e2c2c]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FF8900]/10 border border-[#FF8900]/25 text-[#FF8900] text-xs font-semibold tracking-wider uppercase mb-4">
              Core Capabilities
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-4">
              Career coaching grounded in code, not claims.
            </h2>
            <p className="text-[#a8a3a3] leading-relaxed">
              Every assessment is derived from real repository evidence compared against
              actual employer requirements.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((f) => (
              <FeatureCard key={f.title} {...f} />
            ))}
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section id="how-it-works" className="py-20 lg:py-24 border-t border-[#2e2c2c] bg-[#1e1d1d]/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FF8900]/10 border border-[#FF8900]/25 text-[#FF8900] text-xs font-semibold tracking-wider uppercase mb-4">
              Workflow
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-4">
              Four steps to evidence-based career clarity.
            </h2>
            <p className="text-[#a8a3a3] leading-relaxed">
              From selecting a target role to continuous portfolio improvement — each step
              produces real, verifiable data.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((step) => {
              const StepIcon = step.icon
              return (
                <div
                  key={step.number}
                  className="relative rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6 group hover:border-[#FF8900]/30 transition-all"
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl font-extrabold text-[#FF8900]/20 group-hover:text-[#FF8900]/40 transition-colors">
                      {step.number}
                    </span>
                    <div className="p-2 rounded-lg bg-[#1c1b1b] border border-[#383636] text-[#FF8900]">
                      <StepIcon className="w-4 h-4" />
                    </div>
                  </div>
                  <h3 className="text-base font-semibold text-white mb-2">{step.title}</h3>
                  <p className="text-sm text-[#a8a3a3] leading-relaxed">{step.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ─── BENEFITS ─── */}
      <section id="benefits" className="py-20 lg:py-24 border-t border-[#2e2c2c]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-4">
              Why evidence-based coaching?
            </h2>
            <p className="text-[#a8a3a3] leading-relaxed">
              Traditional career tools rely on self-reported skills. Parivartan AI replaces
              assumptions with verifiable portfolio evidence.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {benefits.map((b) => (
              <div
                key={b.title}
                className="rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6 flex flex-col"
              >
                <div className="p-2.5 rounded-xl bg-[#1c1b1b] border border-[#383636] text-[#FF8900] w-fit mb-4">
                  <b.icon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-white mb-2">{b.title}</h3>
                <p className="text-sm text-[#a8a3a3] leading-relaxed flex-1">{b.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FINAL CTA ─── */}
      <section className="py-20 lg:py-24 border-t border-[#2e2c2c] bg-[#1e1d1d]/40">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-4">
            Ready to prove your skills with code?
          </h2>
          <p className="text-[#a8a3a3] leading-relaxed mb-8 max-w-xl mx-auto">
            Create your free account and discover how your GitHub portfolio stacks up against
            real job requirements.
          </p>
          <button
            onClick={handleGetStarted}
            className="group inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-[#FF8900] hover:bg-[#e67a00] text-black font-semibold text-base transition-all shadow-lg shadow-[#FF8900]/20 cursor-pointer border-none"
          >
            {user ? 'Go to Dashboard' : 'Create Your Account'}
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </section>

      <Footer />
    </div>
  )
}
