import type { LucideIcon } from 'lucide-react'
import { Construction } from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'

interface PlaceholderPageProps {
  title: string
  description: string
  icon?: LucideIcon
}

export function PlaceholderPage({
  title,
  description,
  icon: Icon = Construction,
}: PlaceholderPageProps) {
  return (
    <div className="mx-auto max-w-3xl">
      <Card padding="lg">
        <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-muted)]">
            <Icon className="h-6 w-6 text-[var(--color-accent)]" />
          </div>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-semibold text-[var(--color-text)]">{title}</h1>
              <Badge variant="accent">Coming in a future build</Badge>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-[var(--color-text-muted)]">
              {description}
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}
