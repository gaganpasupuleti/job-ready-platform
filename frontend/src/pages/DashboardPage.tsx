import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, ArrowUpRight, Terminal } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { EmptyState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { useAuth } from '@/hooks/useAuth'
import { fetchCodingProgress } from '@/services/codingService'
import { fetchContinueLearning } from '@/services/learnService'
import { fetchMistakeSummary } from '@/services/mistakeService'
import { fetchReadiness } from '@/services/readinessService'
import { fetchSqlProgress } from '@/services/sqlService'

export function DashboardPage() {
  const { user } = useAuth()
  const uid = user?.id
  const { data: continueItems, isLoading: continueLoading } = useQuery({
    queryKey: ['continue-learning', uid],
    queryFn: fetchContinueLearning,
    enabled: Boolean(uid),
  })
  const { data: coding } = useQuery({
    queryKey: ['coding-progress', uid],
    queryFn: fetchCodingProgress,
    enabled: Boolean(uid),
  })
  const { data: sql } = useQuery({
    queryKey: ['sql-progress', uid],
    queryFn: fetchSqlProgress,
    enabled: Boolean(uid),
  })
  const { data: readiness } = useQuery({
    queryKey: ['readiness', uid],
    queryFn: fetchReadiness,
    enabled: Boolean(uid),
  })
  const { data: mistakeSummary } = useQuery({
    queryKey: ['mistakes-summary', uid],
    queryFn: fetchMistakeSummary,
    enabled: Boolean(uid),
  })

  const nextAction = readiness?.recommended_actions?.[0]
  const primary = continueItems?.[0]
  const showScore =
    readiness?.overall_score_ready === true &&
    readiness.has_minimum_evidence &&
    readiness.score != null
  const displayName = user?.full_name?.split(' ')[0] || user?.username || 'there'

  return (
    <div className="home-v4">
      <div className="home-heading">
        <div>
          <p className="eyebrow">Your learning desk</p>
          <h1>A little practice. Real progress.</h1>
          <p>
            Welcome back, {displayName}.
            {readiness?.target_role?.name
              ? ` Target role: ${readiness.target_role.name}.`
              : ' Your next step is ready.'}
          </p>
        </div>
        <Link to="/practice/python">
          <Button variant="secondary" className="inline-flex items-center gap-2">
            <Terminal className="h-4 w-4" aria-hidden />
            Open playground
            <ArrowUpRight className="h-4 w-4" aria-hidden />
          </Button>
        </Link>
      </div>

      <div className="desk-grid">
        <div className="desk-primary">
          <section className="lesson-feature">
            <div className="feature-kicker">
              <span>{primary?.subtitle || 'Continue learning'}</span>
              <span>
                {primary ? `${primary.progress_percent}%` : 'Pick a path'}
              </span>
            </div>
            <div className="feature-content">
              <div className="feature-copy">
                <span className="overline">Continue your path</span>
                {continueLoading ? (
                  <LoadingState label="Loading continue learning" />
                ) : primary ? (
                  <>
                    <h2>{primary.title}</h2>
                    <p>{primary.subtitle || 'Pick up where you left off'}</p>
                    <span className="feature-description">
                      Live progress from your account — not a preview fixture.
                    </span>
                    <Link to={primary.href}>
                      <Button variant="primary" className="inline-flex items-center gap-2">
                        Continue
                        <ArrowRight className="h-4 w-4" aria-hidden />
                      </Button>
                    </Link>
                  </>
                ) : (
                  <>
                    <h2>Start where it matters.</h2>
                    <p>No recent learning activity yet</p>
                    <span className="feature-description">
                      Open Practice or Learn to begin a course, path, or problem set.
                    </span>
                    <div className="flex flex-wrap gap-2">
                      <Link to="/practice">
                        <Button variant="primary">Open practice</Button>
                      </Link>
                      <Link to="/learn">
                        <Button variant="secondary">Browse learn</Button>
                      </Link>
                    </div>
                  </>
                )}
              </div>
            </div>
          </section>

          {(continueItems?.length ?? 0) > 1 && (
            <section>
              <h2 className="mb-2 text-sm font-semibold text-[var(--color-text)]">Up next</h2>
              <div className="queue-list">
                {continueItems!.slice(1, 5).map((item) => (
                  <Link key={item.href} to={item.href} className="queue-row">
                    <div>
                      <strong>{item.title}</strong>
                      {item.subtitle ? <span className="mt-0.5 block">{item.subtitle}</span> : null}
                    </div>
                    <span>{item.progress_percent}%</span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {!continueLoading && (continueItems?.length ?? 0) === 0 && (
            <EmptyState
              title="No recent learning activity"
              description="Start a course, project, or practice path to see it here."
            />
          )}

          <section>
            <h2 className="mb-2 text-sm font-semibold text-[var(--color-text)]">Practice queue</h2>
            <div className="queue-list">
              <Link to="/practice/sql" className="queue-row">
                <div>
                  <strong>SQL practice</strong>
                  <span className="mt-0.5 block">
                    {sql
                      ? `${sql.solved_count} / ${sql.total_problems} solved`
                      : 'Catalog and workbench'}
                  </span>
                </div>
                <span>SQL</span>
              </Link>
              <Link to="/practice/dsa" className="queue-row">
                <div>
                  <strong>DSA / coding</strong>
                  <span className="mt-0.5 block">
                    {coding
                      ? `${coding.solved_count} / ${coding.total_problems} solved`
                      : 'Assessed problems'}
                  </span>
                </div>
                <span>Code</span>
              </Link>
              <Link to="/practice/aptitude" className="queue-row">
                <div>
                  <strong>Assessments</strong>
                  <span className="mt-0.5 block">Aptitude / CRT exams with server grading</span>
                </div>
                <span>Exam</span>
              </Link>
            </div>
          </section>
        </div>

        <aside className="desk-aside">
          <div className="desk-card">
            <h3>Readiness</h3>
            <p className="text-2xl font-semibold text-[var(--color-text)]">
              {showScore ? `${Math.round(readiness!.score!)}%` : 'Building'}
            </p>
            <p>
              {showScore
                ? 'Based on verified practice — not a hiring probability.'
                : 'Need more verified evidence before a readiness score.'}
            </p>
            {(readiness?.strong_skills?.length ?? 0) > 0 && (
              <p className="mt-2">
                Strong: {readiness!.strong_skills.slice(0, 3).join(', ')}
              </p>
            )}
            {(readiness?.missing_skills?.length ?? 0) > 0 && (
              <p className="mt-1">
                Needs evidence: {readiness!.missing_skills.slice(0, 3).join(', ')}
              </p>
            )}
            <Link
              to="/readiness"
              className="mt-3 inline-block text-xs font-medium text-[var(--color-accent)] hover:underline"
            >
              Open readiness →
            </Link>
          </div>

          <div className="desk-card">
            <h3>Today&apos;s focus</h3>
            <ul>
              {nextAction ? <li>{nextAction.title}</li> : <li>Complete one practice session</li>}
              <li>
                Review mistakes ({mistakeSummary?.open_count ?? 0} open)
              </li>
              <li>Keep a playground draft for warm-up</li>
            </ul>
            {nextAction ? (
              <Link to={nextAction.href} className="mt-3 inline-block">
                <Button variant="secondary" size="sm">
                  {nextAction.title}
                </Button>
              </Link>
            ) : (
              <Link to="/mistakes" className="mt-3 inline-block">
                <Button variant="secondary" size="sm">
                  Open review
                </Button>
              </Link>
            )}
          </div>

          <div className="desk-card">
            <h3>Jobs portal</h3>
            <p>Live listings and applications from your account.</p>
            <Link to="/jobs" className="mt-3 inline-block text-xs font-medium text-[var(--color-accent)]">
              Open Jobs →
            </Link>
          </div>
        </aside>
      </div>
    </div>
  )
}
