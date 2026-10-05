import { useCallback, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { GoogleSignInButton } from '@/components/auth/GoogleSignInButton'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { JOBS_HOME, JOBS_ONBOARDING_KEY, JOBS_PREFERENCES } from '@/components/navigation/navConfig'
import { useAuth } from '@/hooks/useAuth'
import { useRegistrationOpen } from '@/hooks/useRegistrationOpen'
import { googleDestination } from '@/lib/googleAuth'

const FIELD_META = {
  email: { label: 'Email', type: 'email', required: true, autoComplete: 'email' },
  username: { label: 'Username', type: 'text', required: true, autoComplete: 'username' },
  full_name: { label: 'Full name', type: 'text', required: false, autoComplete: 'name' },
  password: { label: 'Password', type: 'password', required: true, autoComplete: 'new-password' },
} as const

export function RegisterPage() {
  const { register, loginWithGoogle } = useAuth()
  const registration = useRegistrationOpen()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleGoogle = useCallback(
    async (credential: string) => {
      setLoading(true)
      setError(null)
      try {
        const response = await loginWithGoogle(credential)
        if (response.is_new_user) sessionStorage.setItem(JOBS_ONBOARDING_KEY, '1')
        navigate(googleDestination(Boolean(response.is_new_user), response.is_new_user ? JOBS_PREFERENCES : JOBS_HOME), {
          replace: true,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Google sign-in failed')
      } finally {
        setLoading(false)
      }
    },
    [loginWithGoogle, navigate],
  )

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      sessionStorage.setItem(JOBS_ONBOARDING_KEY, '1')
      await register(form)
      navigate(JOBS_PREFERENCES, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  if (registration.pending || !registration.open) {
    return (
      <div className="flex min-h-full items-center justify-center bg-[var(--color-surface-muted)] p-4">
        <Card className="w-full max-w-md" padding="lg">
          <h1 className="text-xl font-semibold text-[var(--color-text)]">
            {registration.pending ? 'Checking registration' : 'Registration is closed'}
          </h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            {registration.pending ? 'Loading...' : 'Account creation is unavailable. Contact your instructor.'}
          </p>
          <p className="mt-4 text-center text-xs text-[var(--color-text-muted)]">
            <Link to="/login" className="text-[var(--color-accent)] hover:underline">
              Sign in
            </Link>
          </p>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-[var(--color-surface-muted)] p-4">
      <Card className="w-full max-w-md" padding="lg">
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Create account</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">Start your job preparation journey</p>
        <div className="mt-6">
          <GoogleSignInButton disabled={loading} onCredential={handleGoogle} />
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {(Object.keys(FIELD_META) as Array<keyof typeof FIELD_META>).map((field) => {
            const meta = FIELD_META[field]
            const id = `register-${field}`
            return (
              <div key={field}>
                <label htmlFor={id} className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]">
                  {meta.label}
                </label>
                <input
                  id={id}
                  type={meta.type}
                  required={meta.required}
                  autoComplete={meta.autoComplete}
                  value={form[field]}
                  onChange={(e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))}
                  className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
                />
              </div>
            )
          })}
          {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
          <Button type="submit" variant="primary" className="w-full" disabled={loading}>
            {loading ? 'Creating account...' : 'Register'}
          </Button>
        </form>
        <p className="mt-4 text-center text-xs text-[var(--color-text-muted)]">
          Already have an account?{' '}
          <Link to="/login" className="text-[var(--color-accent)] hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  )
}
