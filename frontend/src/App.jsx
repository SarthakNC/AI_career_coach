
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import DashboardLayout from './components/DashboardLayout'
import LandingPage from './pages/LandingPage'
import SignupPage from './pages/SignupPage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import JobAnalysisPage from './pages/JobAnalysisPage'
import GitHubPortfolioPage from './pages/GitHubPortfolioPage'
import SkillGapAssessmentPage from './pages/SkillGapAssessmentPage'
import RepositoryActivityPage from './pages/RepositoryActivityPage'
import ComingSoonPage from './pages/ComingSoonPage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Protected dashboard routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="jobs" element={<JobAnalysisPage />} />
            <Route path="github" element={<GitHubPortfolioPage />} />
            <Route path="activity" element={<RepositoryActivityPage />} />
            <Route path="skills" element={<SkillGapAssessmentPage />} />
            <Route path="settings" element={<ComingSoonPage />} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
