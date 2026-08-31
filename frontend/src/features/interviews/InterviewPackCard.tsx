import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import type { InterviewPack } from '@/types/interview'

export function InterviewPackCard({
  pack,
  to,
  action,
}: {
  pack: InterviewPack
  to?: string
  action?: ReactNode
}) {
  const href = to ?? `/interviews/packs/${pack.slug}`
  return (
    <Card padding="md" className="flex flex-col gap-3">
      <div className="flex flex-1 flex-col gap-2">
        <Link to={href} className="font-medium text-[var(--color-text)] hover:underline">
          {pack.title}
        </Link>
        {pack.description && (
          <p className="text-sm text-[var(--color-text-muted)] line-clamp-2">{pack.description}</p>
        )}
        <div className="flex flex-wrap gap-1">
          <Badge>{pack.question_count} questions</Badge>
          {pack.experience_level && <Badge>{pack.experience_level}</Badge>}
        </div>
      </div>
      {action}
    </Card>
  )
}
