import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Card, CardHeader } from '@/components/common/Card'
import { EmptyState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { StatCard } from '@/features/dashboard/StatCard'
import { fetchAiHome } from '@/services/aiService'
import { fetchCodingProgress } from '@/services/codingService'
import { fetchInterviewProgress } from '@/services/interviewService'
import { fetchJobsSummary } from '@/services/jobService'
import { fetchReadiness } from '@/services/readinessService'
import { fetchMistakeSummary } from '@/services/mistakeService'
import { fetchContinueLearning, fetchProjects } from '@/services/learnService'
import { fetchSqlProgress } from '@/services/sqlService'
import type { DashboardCard } from '@/types'

export function DashboardPage() {
  const { data: continueItems, isLoading: continueLoading } = useQuery({
    queryKey: ['continue-learning'],
    queryFn: fetchContinueLearning,
  })
  const { data: coding } = useQuery({ queryKey: ['coding-progress'], queryFn: fetchCodingProgress })
  const { data: sql } = useQuery({ queryKey: ['sql-progress'], queryFn: fetchSqlProgress })
  const { data: ai } = useQuery({ queryKey: ['ai-home'], queryFn: fetchAiHome })
  const { data: projects } = useQuery({ queryKey: ['projects'], queryFn: fetchProjects })
  const { data: interview } = useQuery({
    queryKey: ['interview-progress'],
    queryFn: fetchInterviewProgress,
  })
  const { data: jobsSummary } = useQuery({
    queryKey: ['jobs-summary'],
    queryFn: fetchJobsSummary,
  })
  const { data: readiness } = useQuery({ queryKey: ['readiness'], queryFn: fetchReadiness })
  const { data: mistakeSummary } = useQuery({
    queryKey: ['mistakes-summary'],
    queryFn: fetchMistakeSummary,
  })

  const cards: DashboardCard[] = [
    {
      id: 'coding-progress',
      title: 'Coding Progress',
      value: coding ? `${coding.solved_count} / ${coding.total_problems}` : '—',
      subtitle: coding ? 'problems solved' : 'No coding progress yet',
    },
    {
      id: 'sql-progress',
      title: 'SQL Progress',
      value: sql ? `${sql.solved_count} / ${sql.total_problems}` : '—',
      subtitle: sql ? 'problems solved' : 'No SQL progress yet',
    },
    {
      id: 'ai-progress',
      title: 'AI Progress',
      value: ai ? `${ai.prompt_progress.mastered} mastered` : '—',
      subtitle: ai ? `${ai.prompt_progress.attempted} prompt challenges attempted` : 'No AI practice yet',
    },
    {
      id: 'interview-progress',
      title: 'Interview Progress',
      value: interview ? String(interview.questions_reviewed) : '—',
      subtitle: interview
        ? `${interview.needs_review} need review · ${interview.sessions_completed} sessions`
        : 'No interview progress yet',
    },
    {
      id: 'project-progress',
      title: 'Project Progress',
      value:
        projects && projects.length
          ? `${Math.round(projects.reduce((sum, p) => sum + p.progress_percent, 0) / projects.length)}%`
          : '—',
      subtitle: projects?.length ? `${projects.length} projects` : 'No project progress yet',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-[var(--color-text)]">Welcome back</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Continue learning, practice stats, target role readiness, and recommended next actions.
        </p>
      </div>

      {(readiness?.recommended_actions?.length ?? 0) > 0 && (
        <Card>
          <CardHeader title="Recommended Next" />
          <Link
            to={readiness!.recommended_actions[0].href}
            className="block rounded-md border border-[var(--color-border)] p-3 hover:border-[var(--color-accent)]"
          >
            <p className="text-sm font-medium">{readiness!.recommended_actions[0].title}</p>
            <p className="text-xs text-[var(--color-text-muted)]">
              {readiness!.recommended_actions[0].reason}
            </p>
          </Link>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Link to="/readiness" className="block">
          <Card>
            <CardHeader title="Target Role Readiness" />
            <p className="text-2xl font-semibold">
              {readiness?.has_minimum_evidence && readiness.score != null
                ? `${Math.round(readiness.score)}%`
                : 'Building profile'}
            </p>
            <p className="text-xs text-[var(--color-text-muted)]">
              {readiness?.target_role?.name ?? 'Set target role in Jobs'}
            </p>
          </Card>
        </Link>
        <Link to="/mistakes" className="block">
          <Card>
            <CardHeader title="Mistakes to Review" />
            <p className="text-2xl font-semibold">{mistakeSummary?.open_count ?? 0}</p>
            <p className="text-xs text-[var(--color-text-muted)]">open items</p>
          </Card>
        </Link>
      </div>

      {continueLoading && <LoadingState label="Loading continue learning" />}
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
      {!continueLoading && (continueItems?.length ?? 0) === 0 && (
        <EmptyState
          title="No recent learning activity"
          description="Start a course, project, or practice path to see it here."
        />
      )}

      {jobsSummary && (
        <Card>
          <CardHeader
            title="Job search"
            description={`${jobsSummary.saved_count} saved · ${jobsSummary.applications_total} applications · ${jobsSummary.follow_ups_due} follow-ups due`}
            action={
              <Link to="/jobs" className="text-sm text-[var(--color-accent)] hover:underline">
                Open jobs hub
              </Link>
            }
          />
          <div className="grid gap-3 sm:grid-cols-4 text-sm">
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Applied</p>
              <p className="font-semibold text-[var(--color-text)]">{jobsSummary.applied_count}</p>
            </div>
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Interviews</p>
              <p className="font-semibold text-[var(--color-text)]">{jobsSummary.interview_count}</p>
            </div>
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Offers</p>
              <p className="font-semibold text-[var(--color-text)]">{jobsSummary.offer_count}</p>
            </div>
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Overdue follow-ups</p>
              <p className="font-semibold text-[var(--color-text)]">{jobsSummary.follow_ups_overdue}</p>
            </div>
          </div>
        </Card>
      )}

      {interview && (interview.questions_reviewed > 0 || interview.needs_review > 0) && (
        <Card>
          <CardHeader
            title="Interview prep"
            description={`${interview.questions_reviewed} reviewed · ${interview.needs_review} need review`}
            action={
              <Link to="/interviews" className="text-sm text-[var(--color-accent)] hover:underline">
                Continue
              </Link>
            }
          />
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
        {cards.map((card) => (
          <StatCard key={card.id} card={card} />
        ))}
      </div>
    </div>
  )
}
