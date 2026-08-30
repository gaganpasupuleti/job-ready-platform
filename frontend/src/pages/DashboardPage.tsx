import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Card, CardHeader } from '@/components/common/Card'
import { StatCard } from '@/features/dashboard/StatCard'
import {
  mockDashboardCards,
  mockUpcomingAssessments,
  mockWeakSkills,
} from '@/mocks/dev-data'
import { fetchContinueLearning } from '@/services/learnService'
import { formatPercent } from '@/utils/cn'

export function DashboardPage() {
  const { data: continueItems } = useQuery({
    queryKey: ['continue-learning'],
    queryFn: fetchContinueLearning,
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Welcome back</h2>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Your job preparation overview. Continue Learning uses live course progress; other cards may still use
          sample data.
        </p>
      </div>

      {(continueItems?.length ?? 0) > 0 && (
        <Card>
          <CardHeader title="Continue Learning" description="Pick up where you left off" />
          <div className="grid gap-3 sm:grid-cols-2">
            {continueItems!.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className="rounded-md border border-[var(--color-border)] p-3 hover:border-[var(--color-accent)]"
              >
                <p className="text-sm font-medium text-[var(--color-text)]">{item.title}</p>
                {item.subtitle && (
                  <p className="text-xs text-[var(--color-text-muted)]">{item.subtitle}</p>
                )}
                <p className="mt-1 text-xs text-[var(--color-text-subtle)]">{item.progress_percent}%</p>
              </Link>
            ))}
          </div>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {mockDashboardCards.map((card) => (
          <StatCard key={card.id} card={card} />
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="Weak Skills"
            description="Focus areas based on recent practice performance"
          />
          <ul className="space-y-3">
            {mockWeakSkills.map((item) => (
              <li key={item.skill}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="text-[var(--color-text)]">{item.skill}</span>
                  <span className="text-[var(--color-text-muted)]">
                    {formatPercent(item.score)}
                  </span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-[var(--color-surface-muted)]">
                  <div
                    className="h-full rounded-full bg-[var(--color-accent)]"
                    style={{ width: `${item.score}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <CardHeader title="Upcoming Assessments" description="Scheduled tests and contests" />
          <ul className="divide-y divide-[var(--color-border)]">
            {mockUpcomingAssessments.map((assessment) => (
              <li
                key={assessment.id}
                className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"
              >
                <div>
                  <p className="text-sm font-medium text-[var(--color-text)]">
                    {assessment.title}
                  </p>
                  <p className="text-xs text-[var(--color-text-muted)]">{assessment.type}</p>
                </div>
                <span className="shrink-0 text-xs text-[var(--color-text-subtle)]">
                  {assessment.date}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <p className="text-sm">
        <Link to="/practice" className="text-[var(--color-accent)] hover:underline">
          Open Practice Hub →
        </Link>
      </p>
    </div>
  )
}
