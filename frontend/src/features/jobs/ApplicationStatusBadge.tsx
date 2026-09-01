import { Badge } from '@/components/common/Badge'
import type { ApplicationStatus } from '@/types/job'

const STATUS_LABELS: Record<ApplicationStatus, string> = {
  saved: 'Saved',
  preparing: 'Preparing',
  applied: 'Applied',
  screening: 'Screening',
  assessment: 'Assessment',
  interview: 'Interview',
  offer: 'Offer',
  rejected: 'Rejected',
  withdrawn: 'Withdrawn',
  accepted: 'Accepted',
  ghosted: 'Ghosted',
}

const STATUS_VARIANT: Record<
  ApplicationStatus,
  'default' | 'accent' | 'success' | 'warning'
> = {
  saved: 'default',
  preparing: 'accent',
  applied: 'accent',
  screening: 'accent',
  assessment: 'accent',
  interview: 'accent',
  offer: 'success',
  rejected: 'warning',
  withdrawn: 'default',
  accepted: 'success',
  ghosted: 'warning',
}

export function applicationStatusLabel(status: ApplicationStatus | string) {
  return STATUS_LABELS[status as ApplicationStatus] ?? status.replace(/_/g, ' ')
}

export function ApplicationStatusBadge({ status }: { status: ApplicationStatus | string }) {
  const variant = STATUS_VARIANT[status as ApplicationStatus] ?? 'default'
  return <Badge variant={variant}>{applicationStatusLabel(status)}</Badge>
}
