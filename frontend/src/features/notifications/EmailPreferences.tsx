import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { fetchEmailPreferences, updateEmailPreferences, type EmailPreferences } from '@/services/notificationService'

export function EmailPreferences({ userId }: { userId: string }) {
  const queryClient = useQueryClient()
  const preferences = useQuery({
    queryKey: ['email-preferences', userId],
    queryFn: fetchEmailPreferences,
  })
  const save = useMutation({
    mutationFn: updateEmailPreferences,
    onSuccess: (data) => {
      queryClient.setQueryData(['email-preferences', userId], data)
    },
  })

  async function toggle(key: keyof EmailPreferences) {
    const current = preferences.data
    if (!current || save.isPending) return
    try {
      await save.mutateAsync({ [key]: !current[key] })
    } catch {
      return
    }
  }

  return (
    <fieldset className="notification-email">
      <h3>Email</h3>
      <p className="text-xs text-[var(--color-text-muted)]">
        Turning email off leaves notifications in this list.
      </p>
      {preferences.isError ? (
        <div className="space-y-2">
          <ErrorState message={preferences.error instanceof Error ? preferences.error.message : 'Could not load email preferences.'} />
          <Button type="button" variant="secondary" size="sm" onClick={() => void preferences.refetch()}>
            Retry
          </Button>
        </div>
      ) : null}
      <label>
        <input
          type="checkbox"
          checked={preferences.data?.assignment_review_enabled ?? false}
          disabled={!preferences.data || save.isPending}
          onChange={() => void toggle('assignment_review_enabled')}
        />
        Email me when an assignment is reviewed
      </label>
      <label>
        <input
          type="checkbox"
          checked={preferences.data?.support_reply_enabled ?? false}
          disabled={!preferences.data || save.isPending}
          onChange={() => void toggle('support_reply_enabled')}
        />
        Email me when support replies
      </label>
      {save.isError ? (
        <p className="text-sm text-[var(--color-danger)]">
          {save.error instanceof Error ? save.error.message : 'Could not save email preferences.'}
        </p>
      ) : null}
    </fieldset>
  )
}
