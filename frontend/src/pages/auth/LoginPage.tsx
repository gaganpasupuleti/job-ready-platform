import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { useAuth } from '@/hooks/useAuth'
import { DEV_AUTO_LOGIN } from '@/mocks/dev-auth'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState(DEV_AUTO_LOGIN?.email ?? '')
  const [password, setPassword] = useState(DEV_AUTO_LOGIN?.password ?? '')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const fromQuery = new URLSearchParams(location.search).get('from')
  const from =
    (location.state as { from?: string } | null)?.from ??
    (fromQuery && fromQuery.startsWith('/') ? fromQuery : null) ??
    '/'

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const credentials = {
        email: email.trim() || DEV_AUTO_LOGIN?.email || '',
        password: password || DEV_AUTO_LOGIN?.password || '',
      }
      await login(credentials)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-[var(--color-surface-muted)] p-4">
      <Card className="w-full max-w-md" padding="lg">
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Sign in</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Access your Job Ready Platform account
        </p>
        {DEV_AUTO_LOGIN && (
          <p className="mt-2 rounded-md border border-dashed border-[var(--color-border)] bg-[var(--color-surface-muted)] px-3 py-2 text-xs text-[var(--color-text-subtle)]">
            Dev mode: credentials pre-filled — click Sign in to auto-login.
          </p>
        )}
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label htmlFor="login-email" className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]">
              Email
            </label>
            <input
              id="login-email"
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="login-password" className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            />
          </div>
          {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
          <Button type="submit" variant="primary" className="w-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
        <p className="mt-4 text-center text-xs text-[var(--color-text-muted)]">
          No account?{' '}
          <Link to="/register" className="text-[var(--color-accent)] hover:underline">
            Register
          </Link>
        </p>
      </Card>
    </div>
  )
}
