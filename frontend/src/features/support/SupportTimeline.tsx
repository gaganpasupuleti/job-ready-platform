import type { SupportTimelineItem } from '@/services/supportService'
import { SUPPORT_STATUSES, supportLabel } from '@/services/supportService'

export function SupportTimeline({ items }: { items: SupportTimelineItem[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-[var(--color-text-muted)]">No replies yet.</p>
  }
  return (
    <ol className="space-y-3">
      {items.map((item) => (
        <li key={item.id} className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-sm">
          <p className="font-medium text-[var(--color-text)]">
            {item.author_name}
            <span className="font-normal text-[var(--color-text-muted)]"> · {item.author_role}</span>
          </p>
          <p className="text-xs text-[var(--color-text-muted)]">{new Date(item.created_at).toLocaleString()}</p>
          {item.kind === 'status' ? (
            <p className="mt-1">
              Status changed from {supportLabel(SUPPORT_STATUSES, item.from_status)} to{' '}
              {supportLabel(SUPPORT_STATUSES, item.to_status)}.
            </p>
          ) : (
            <p className="support-text mt-1">{item.body}</p>
          )}
        </li>
      ))}
    </ol>
  )
}
