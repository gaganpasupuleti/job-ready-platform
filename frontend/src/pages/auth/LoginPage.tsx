import { useCallback, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { GoogleSignInButton } from '@/components/auth/GoogleSignInButton'
import { Logo } from '@/components/brand/Logo'
import { Button } from '@/components/common/Button'
import { FieldLabel, Input } from '@/components/common/Field'
import { useAuth } from '@/hooks/useAuth'
import { useRegistrationOpen } from '@/hooks/useRegistrationOpen'
import { JOBS_HOME, JOBS_ONBOARDING_KEY } from '@/components/navigation/navConfig'
import { googleDestination } from '@/lib/googleAuth'
import { DEV_AUTO_LOGIN } from '@/mocks/dev-auth'

export function LoginPage() {
  const { login, loginWithGoogle } = useAuth()
  const registration = useRegistrationOpen()
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
    JOBS_HOME

  const handleGoogle = useCallback(
    async (credential: string) => {
      setLoading(true)
      setError(null)
      try {
        const response = await loginWithGoogle(credential)
        if (response.is_new_user) sessionStorage.setItem(JOBS_ONBOARDING_KEY, '1')
        navigate(googleDestination(Boolean(response.is_new_user), from), { replace: true })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Google sign-in failed')
      } finally {
        setLoading(false)
      }
    },
    [from, loginWithGoogle, navigate],
  )

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
    <div className="auth-shell">
      <div className="auth-shell-inner">
        <aside className="auth-shell-aside" aria-hidden={false}>
          <Link to="/" className="auth-shell-brand">
            <Logo />
          </Link>
          <h1>Your job prep workspace</h1>
          <p>Practice, roadmaps, library resources, and live job listings in one place—built for students and career switchers.</p>
          <ul className="auth-shell-points">
            <li>Track applications and saved roles</li>
            <li>SQL, coding, and aptitude practice</li>
            <li>Official career roadmaps and reading lists</li>
          </ul>
        </aside>

        <div>
          <div className="auth-shell-mobile-brand">
            <Link to="/" className="auth-shell-brand" aria-label="JobReady home">
              <Logo />
            </Link>
          </div>
          <section className="auth-shell-card" aria-labelledby="login-heading">
            <h2 id="login-heading">Sign in</h2>
            <p className="auth-lead">Use your school or work email to continue.</p>
            {DEV_AUTO_LOGIN ? (
              <p className="auth-dev-banner" role="status">
                Dev mode: credentials pre-filled — click Sign in to auto-login.
              </p>
            ) : null}
            <div className="mt-5">
              <GoogleSignInButton disabled={loading} onCredential={handleGoogle} />
            </div>
            <p className="auth-divider" aria-hidden>or email</p>
            <form onSubmit={handleSubmit} className="space-y-4">
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
              {error ? (
                <p className="text-xs text-[var(--color-danger)]" role="alert">
                  {error}
                </p>
              ) : null}
              <Button type="submit" variant="primary" className="w-full" disabled={loading}>
                {loading ? 'Signing in…' : 'Sign in'}
              </Button>
            </form>
            {registration.open ? (
              <p className="auth-footer-link">
                No account? <Link to="/register">Create one</Link>
              </p>
            ) : null}
          </section>
        </div>
      </div>
    </div>
  )
}
