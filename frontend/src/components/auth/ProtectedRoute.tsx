import { Navigate, useLocation } from 'react-router-dom'

import { JOBS_ONBOARDING_KEY, JOBS_PREFERENCES } from '@/components/navigation/navConfig'
import { useAuth } from '@/hooks/useAuth'
import { googleDestination } from '@/lib/googleAuth'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-[var(--color-text-muted)]">
        Loading...
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return children
}

export function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()

  if (isLoading) return null
  if (!user || (user.role !== 'admin' && user.role !== 'trainer')) {
    return <Navigate to="/" replace />
  }

  return children
}

export function GuestRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return null
  if (isAuthenticated) {
    const onboarding =
      typeof sessionStorage !== 'undefined' && sessionStorage.getItem(JOBS_ONBOARDING_KEY) === '1'
    if (onboarding) return <Navigate to={JOBS_PREFERENCES} replace />
    const fromState = (location.state as { from?: string } | null)?.from ?? null
    const fromQuery = new URLSearchParams(location.search).get('from')
    return <Navigate to={googleDestination(false, fromState ?? fromQuery)} replace />
  }
  return children
}
