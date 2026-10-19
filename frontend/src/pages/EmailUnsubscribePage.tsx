import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { unsubscribeEmail } from '@/services/notificationService'

export function EmailUnsubscribePage() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  async function confirm() {
    setPending(true)
    setError('')
    try {
      const saved = await unsubscribeEmail(token)
      const stopped = !saved.assignment_review_enabled || !saved.support_reply_enabled
      setMessage(stopped ? 'These emails are now off. Notifications in JobReady are unchanged.' : 'This email category is off.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not turn off these emails.')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-[var(--color-surface-muted)] p-4">
      <Card className="w-full max-w-md" padding="lg">
        <h1 className="text-xl font-semibold text-[var(--color-text)]">Email preferences</h1>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          This stops one kind of JobReady email. It does not remove notifications inside the app.
        </p>
        {!token ? <p className="mt-4 text-sm text-[var(--color-danger)]">This unsubscribe link is not valid.</p> : null}
        {token && !message ? (
          <Button type="button" className="mt-4" onClick={() => void confirm()} disabled={pending}>
            {pending ? 'Saving' : 'Turn off these emails'}
          </Button>
        ) : null}
        {message ? <p className="mt-4 text-sm text-[var(--color-text)]">{message}</p> : null}
        {error ? <p className="mt-4 text-sm text-[var(--color-danger)]">{error}</p> : null}
      </Card>
    </div>
  )
}
