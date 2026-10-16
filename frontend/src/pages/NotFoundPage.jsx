/**
 * NotFoundPage — 404 fallback.
 */
import { Link } from 'react-router-dom'
import { Home } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-[#232222] flex items-center justify-center px-4">
      <div className="text-center">
        <p className="text-7xl font-extrabold text-[#FF8900] mb-4">404</p>
        <h1 className="text-2xl font-bold text-white mb-2">Page not found</h1>
        <p className="text-sm text-[#9c9797] mb-8 max-w-md mx-auto">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[#FF8900] hover:bg-[#e67a00] text-black font-semibold text-sm transition-colors no-underline"
        >
          <Home className="w-4 h-4" />
          Back to Home
        </Link>
      </div>
    </div>
  )
}
