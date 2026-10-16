/**
 * SignupPage — Create account via Supabase Auth.
 * Stores full_name in user_metadata.
 */
import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Sparkles, Loader2, CheckCircle2, AlertCircle, Eye, EyeOff } from 'lucide-react'

export default function SignupPage() {
  const { user, signUp } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ fullName: '', email: '', password: '', confirmPassword: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState('')
  const [success, setSuccess] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  // Redirect authenticated users
  if (user) return <Navigate to="/dashboard" replace />

  function validate() {
    const e = {}
    if (!form.fullName.trim()) e.fullName = 'Full name is required.'
    if (!form.email.trim()) {
      e.email = 'Email is required.'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      e.email = 'Enter a valid email address.'
    }
    if (!form.password) {
      e.password = 'Password is required.'
    } else if (form.password.length < 8) {
      e.password = 'Password must be at least 8 characters.'
    } else if (!/[A-Z]/.test(form.password)) {
      e.password = 'Include at least one uppercase letter.'
    } else if (!/[0-9]/.test(form.password)) {
      e.password = 'Include at least one number.'
    }
    if (form.password !== form.confirmPassword) {
      e.confirmPassword = 'Passwords do not match.'
    }
    return e
  }

  async function handleSubmit(ev) {
    ev.preventDefault()
    setServerError('')
    const v = validate()
    setErrors(v)
    if (Object.keys(v).length) return

    setLoading(true)
    const { error } = await signUp({
      email: form.email.trim(),
      password: form.password,
      fullName: form.fullName.trim(),
    })
    setLoading(false)

    if (error) {
      setServerError(error.message || 'Signup failed. Please try again.')
    } else {
      setSuccess(true)
    }
  }

  function update(field) {
    return (e) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }))
      setErrors((prev) => ({ ...prev, [field]: undefined }))
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-[#232222] flex items-center justify-center px-4">
        <div className="max-w-md w-full rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#242323] p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto mb-5">
            <CheckCircle2 className="w-8 h-8 text-emerald-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">Account Created!</h2>
          <p className="text-sm text-[#a8a3a3] leading-relaxed mb-6">
            Check your email for a confirmation link. Once confirmed, you can log in and start analyzing your portfolio.
          </p>
          <Link
            to="/login"
            className="inline-block px-6 py-2.5 rounded-lg bg-[#FF8900] hover:bg-[#e67a00] text-black font-semibold text-sm transition-colors no-underline"
          >
            Go to Login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#232222] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        {/* Brand */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 no-underline mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF8900] to-[#b35f00] p-0.5 flex items-center justify-center shadow-lg shadow-[#FF8900]/20">
              <div className="w-full h-full bg-[#232222] rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-[#FF8900]" />
              </div>
            </div>
            <span className="text-xl font-bold text-white">
              CareerProof <span className="text-[#FF8900]">AI</span>
            </span>
          </Link>
          <h1 className="text-2xl font-bold text-white mt-2">Create your account</h1>
          <p className="text-sm text-[#9c9797] mt-1">Start building evidence-based career insights.</p>
        </div>

        {/* Form Card */}
        <div className="rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6 sm:p-8 shadow-xl">
          {serverError && (
            <div className="flex items-start gap-2 mb-5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30">
              <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-rose-300">{serverError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name */}
            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-[#d4cfcf] mb-1.5">
                Full Name
              </label>
              <input
                id="fullName"
                type="text"
                value={form.fullName}
                onChange={update('fullName')}
                placeholder="Your full name"
                className={`w-full px-3.5 py-2.5 rounded-lg bg-[#1c1b1b] border ${errors.fullName ? 'border-rose-500/60' : 'border-[#3a3838]'} text-white text-sm placeholder-[#6b6666] focus:outline-none focus:border-[#FF8900]/60 focus:ring-1 focus:ring-[#FF8900]/30 transition-colors`}
              />
              {errors.fullName && <p className="text-xs text-rose-400 mt-1">{errors.fullName}</p>}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-[#d4cfcf] mb-1.5">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={update('email')}
                placeholder="you@example.com"
                className={`w-full px-3.5 py-2.5 rounded-lg bg-[#1c1b1b] border ${errors.email ? 'border-rose-500/60' : 'border-[#3a3838]'} text-white text-sm placeholder-[#6b6666] focus:outline-none focus:border-[#FF8900]/60 focus:ring-1 focus:ring-[#FF8900]/30 transition-colors`}
              />
              {errors.email && <p className="text-xs text-rose-400 mt-1">{errors.email}</p>}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-[#d4cfcf] mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={update('password')}
                  placeholder="Min. 8 chars, 1 uppercase, 1 number"
                  className={`w-full px-3.5 py-2.5 pr-10 rounded-lg bg-[#1c1b1b] border ${errors.password ? 'border-rose-500/60' : 'border-[#3a3838]'} text-white text-sm placeholder-[#6b6666] focus:outline-none focus:border-[#FF8900]/60 focus:ring-1 focus:ring-[#FF8900]/30 transition-colors`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6b6666] hover:text-[#a8a3a3] bg-transparent border-none cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-xs text-rose-400 mt-1">{errors.password}</p>}
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-[#d4cfcf] mb-1.5">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirm ? 'text' : 'password'}
                  value={form.confirmPassword}
                  onChange={update('confirmPassword')}
                  placeholder="Re-enter your password"
                  className={`w-full px-3.5 py-2.5 pr-10 rounded-lg bg-[#1c1b1b] border ${errors.confirmPassword ? 'border-rose-500/60' : 'border-[#3a3838]'} text-white text-sm placeholder-[#6b6666] focus:outline-none focus:border-[#FF8900]/60 focus:ring-1 focus:ring-[#FF8900]/30 transition-colors`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6b6666] hover:text-[#a8a3a3] bg-transparent border-none cursor-pointer"
                >
                  {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.confirmPassword && <p className="text-xs text-rose-400 mt-1">{errors.confirmPassword}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-[#FF8900] hover:bg-[#e67a00] disabled:opacity-60 disabled:cursor-not-allowed text-black font-semibold text-sm transition-colors cursor-pointer border-none mt-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating Account…
                </>
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          <p className="text-center text-sm text-[#9c9797] mt-5">
            Already have an account?{' '}
            <Link to="/login" className="text-[#FF8900] hover:text-[#ffab42] font-medium no-underline">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
