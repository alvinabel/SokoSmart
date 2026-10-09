import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../lib/auth'
import Spinner from '../ui/Spinner'

export function ProtectedRoute({ children }) {
  const { isAuthenticated, ready } = useAuth()
  const location = useLocation()

  if (!ready) return <Spinner center />
  if (!isAuthenticated) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }
  return children
}

export function RoleRoute({ role, children }) {
  const { user, ready } = useAuth()
  if (!ready) return <Spinner center />
  if (!user) return <Navigate to="/login" replace />
  const allowed = Array.isArray(role) ? role : [role]
  if (!allowed.includes(user.role)) return <Navigate to="/" replace />
  return children
}