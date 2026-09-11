import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { Logo } from '@/components/brand/Logo'
import { Button } from '@/components/common/Button'
import { FieldLabel, Input } from '@/components/common/Field'
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
    <div className="flex min-h-full items-center justify-center bg-[var(--color-surface-muted)] px-4 py-10">
      <div className="w-full max-w-md">
        <div className="new-brand mb-8 justify-center sm:justify-start">
          <Logo />
        </div>
        <section className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 sm:p-8">
          <h1 className="text-xl font-semibold tracking-tight text-[var(--color-text)]">Sign in</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Access your learning desk, practice, and jobs workspace.
          </p>
          {DEV_AUTO_LOGIN && (
            <p className="mt-3 rounded-[var(--radius-control)] border border-dashed border-[var(--color-border)] bg-[var(--color-surface-muted)] px-3 py-2 text-xs text-[var(--color-text-subtle)]">
              Dev mode: credentials pre-filled — click Sign in to auto-login.
            </p>
          )}
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <FieldLabel htmlFor="login-email">Email</FieldLabel>
              <Input
                id="login-email"
                type="email"
                required
                autoComplete="username"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-invalid={Boolean(error)}
              />
            </div>
            <div>
              <FieldLabel htmlFor="login-password">Password</FieldLabel>
              <Input
                id="login-password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={Boolean(error)}
              />
            </div>
            {error && (
              <p className="text-xs text-[var(--color-danger)]" role="alert">
                {error}
              </p>
            )}
            <Button type="submit" variant="primary" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>
          <p className="mt-5 text-center text-xs text-[var(--color-text-muted)]">
            No account?{' '}
            <Link to="/register" className="font-medium text-[var(--color-accent)] hover:underline">
              Register
            </Link>
          </p>
        </section>
      </div>
    </div>
  )
}
