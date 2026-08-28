import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { useAuth } from '@/hooks/useAuth'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await register(form)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-[var(--color-surface-muted)] p-4">
      <Card className="w-full max-w-md" padding="lg">
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Create account</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">Start your job preparation journey</p>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {(['email', 'username', 'full_name', 'password'] as const).map((field) => (
            <div key={field}>
              <label className="mb-1 block text-xs font-medium capitalize text-[var(--color-text-muted)]">
                {field.replace('_', ' ')}
              </label>
              <input
                type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'text'}
                required={field !== 'full_name'}
                value={form[field]}
                onChange={(e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))}
                className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
              />
            </div>
          ))}
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
