import { TrendingDown, TrendingUp } from 'lucide-react'

import { Card } from '@/components/common/Card'
import type { DashboardCard } from '@/types'
import { cn } from '@/utils/cn'

interface StatCardProps {
  card: DashboardCard
}

export function StatCard({ card }: StatCardProps) {
  const TrendIcon =
    card.trendDirection === 'down'
      ? TrendingDown
      : card.trendDirection === 'up'
        ? TrendingUp
        : null

  return (
    <Card padding="sm" className="flex flex-col gap-2">
      <p className="text-xs font-medium text-[var(--color-text-muted)]">{card.title}</p>
      <p className="text-2xl font-semibold tracking-tight text-[var(--color-text)]">
        {card.value}
      </p>
      {card.subtitle && (
        <p className="text-xs text-[var(--color-text-subtle)]">{card.subtitle}</p>
      )}
      {card.trend && (
        <p
          className={cn(
            'flex items-center gap-1 text-xs',
            card.trendDirection === 'up' && 'text-[var(--color-success)]',
            card.trendDirection === 'down' && 'text-[var(--color-danger)]',
            card.trendDirection === 'neutral' && 'text-[var(--color-text-subtle)]',
          )}
        >
          {TrendIcon && <TrendIcon className="h-3 w-3" />}
          {card.trend}
        </p>
      )}
    </Card>
  )
}
