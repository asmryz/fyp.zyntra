import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { homePathForRole, roadmapPathFromStudentPath } from '../utils/roles'
import { PageLoader } from './ui/Feedback'

/**
 * Only renders its pages for logged-in users with one of the allowed roles.
 * This improves the user experience; the backend still checks every request.
 */
export default function ProtectedRoute({ roles }) {
  const { user, status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <PageLoader label="Checking your session..." />

  if (!user) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }

  if (roles && !roles.includes(user.role)) {
    // A program's roadmap link opens that roadmap in the user's own dashboard
    return <Navigate to={roadmapPathFromStudentPath(location.pathname, user.role) || homePathForRole(user.role)} replace />
  }

  return <Outlet />
}
