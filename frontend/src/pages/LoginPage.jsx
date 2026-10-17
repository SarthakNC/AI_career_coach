/**
 * LoginPage — Authenticate via Supabase Auth.
 */
import { useState } from 'react'
import { Link, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { supabase } from '../services/supabase'
import { Sparkles, Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
  const { user, signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [resending, setResending] = useState(false)
  const [resendMsg, setResendMsg] = useState('')

  async function handleResendConfirmation() {
    if (!form.email.trim()) return
    setResending(true)
    setResendMsg('')
    try {
      const { error } = await supabase.auth.resend({
        type: 'signup',
        email: form.email.trim(),
      })
      if (error) {
        setResendMsg(`Failed to resend: ${error.message}`)
      } else {
        setResendMsg('Confirmation email sent! Please check your inbox/spam folder.')
      }
    } catch (err) {
      setResendMsg('Could not resend email. Please try again.')
    } finally {
      setResending(false)
    }
  }

  // Redirect authenticated users
  if (user) {
    const from = location.state?.from?.pathname || '/dashboard'
    return <Navigate to={from} replace />
  }

  function validate() {
    const e = {}
    if (!form.email.trim()) {
      e.email = 'Email is required.'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      e.email = 'Enter a valid email address.'
    }
    if (!form.password) e.password = 'Password is required.'
    return e
  }

  async function handleSubmit(ev) {
    ev.preventDefault()
    setServerError('')
    const v = validate()
    setErrors(v)
    if (Object.keys(v).length) return

    setLoading(true)
    const { error } = await signIn({
      email: form.email.trim(),
      password: form.password,
    })
    setLoading(false)

    if (error) {
      setServerError(error.message || 'Invalid credentials. Please try again.')
    } else {
      const from = location.state?.from?.pathname || '/dashboard'
      navigate(from, { replace: true })
    }
  }

  function update(field) {
    return (e) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }))
      setErrors((prev) => ({ ...prev, [field]: undefined }))
    }
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
              Parivartan <span className="text-[#FF8900]">AI</span>
            </span>
          </Link>
          <h1 className="text-2xl font-bold text-white mt-2">Welcome back</h1>
          <p className="text-sm text-[#9c9797] mt-1">Log in to your Parivartan AI account.</p>
        </div>

        {/* Form Card */}
        <div className="rounded-2xl border border-[#3a3838] bg-gradient-to-b from-[#2a2929] to-[#242323] p-6 sm:p-8 shadow-xl">
          {serverError && (
            <div className="flex flex-col gap-2 mb-5 p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/30">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-rose-300">{serverError}</p>
              </div>
              {serverError.toLowerCase().includes('not confirmed') && (
                <div className="mt-1 pt-2 border-t border-rose-500/20 text-xs text-rose-200/80 space-y-2">
                  <p>
                    Supabase requires email confirmation before logging in. You can check your inbox, or confirm the user in your Supabase dashboard under <strong>Authentication &rarr; Users</strong>.
                  </p>
                  <button
                    type="button"
                    onClick={handleResendConfirmation}
                    disabled={resending}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-[#FF8900]/20 hover:bg-[#FF8900]/30 text-[#FF8900] text-xs font-medium transition-colors border border-[#FF8900]/30 cursor-pointer disabled:opacity-50"
                  >
                    {resending ? 'Sending...' : 'Resend confirmation email'}
                  </button>
                  {resendMsg && <p className="text-emerald-400 mt-1">{resendMsg}</p>}
                </div>
              )}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label htmlFor="login-email" className="block text-sm font-medium text-[#d4cfcf] mb-1.5">
                Email
              </label>
              <input
                id="login-email"
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
              <label htmlFor="login-password" className="block text-sm font-medium text-[#d4cfcf] mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={update('password')}
                  placeholder="Your password"
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

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-[#FF8900] hover:bg-[#e67a00] disabled:opacity-60 disabled:cursor-not-allowed text-black font-semibold text-sm transition-colors cursor-pointer border-none mt-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in…
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className="text-center text-sm text-[#9c9797] mt-5">
            Don't have an account?{' '}
            <Link to="/signup" className="text-[#FF8900] hover:text-[#ffab42] font-medium no-underline">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
