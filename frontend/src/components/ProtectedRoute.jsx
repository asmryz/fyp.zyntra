import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { homePathForRole } from '../utils/roles'
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
    return <Navigate to={homePathForRole(user.role)} replace />
  }

  return <Outlet />
}
