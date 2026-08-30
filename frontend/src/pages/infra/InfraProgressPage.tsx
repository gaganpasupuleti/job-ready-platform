import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Card, CardHeader } from '@/components/common/Card'
import { fetchInfraProgress } from '@/services/infraService'

export function InfraProgressPage({ domain }: { domain: 'cloud' | 'devops' | 'cybersecurity' }) {
  const { data, isLoading } = useQuery({
    queryKey: ['infra-progress', domain],
    queryFn: () => fetchInfraProgress(domain),
  })
  const home = `/${domain}`

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">
          {domain === 'cybersecurity' ? 'Cybersecurity' : domain[0].toUpperCase() + domain.slice(1)} progress
        </h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          MCQ accuracy, scenario attempts, paths, and projects. Not a global job-readiness score.
        </p>
      </div>
      {isLoading && <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>}
      {data && (
        <>
          <Card>
            <CardHeader title="Scenarios" />
            <p className="text-sm">
              Attempted {data.scenario_attempted} · mastered {data.scenario_mastered}
            </p>
          </Card>
          <Card>
            <CardHeader title="By track" />
            <div className="space-y-3">
              {data.topics.map((topic) => (
                <div key={topic.key} className="rounded border border-[var(--color-border)] p-3 text-sm">
                  <p className="font-medium">{topic.label}</p>
                  <p className="text-[var(--color-text-muted)]">
                    MCQ {topic.mcq_attempts} attempts
                    {topic.mcq_accuracy != null ? ` · ${topic.mcq_accuracy}%` : ' · no attempts'}
                  </p>
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <CardHeader title="Weak topics" />
            {data.weak_topics.length ? (
              <ul className="list-disc pl-5 text-sm">
                {data.weak_topics.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[var(--color-text-muted)]">No weak topics yet.</p>
            )}
            <div className="mt-3 flex flex-wrap gap-3 text-sm">
              <Link to={home} className="text-[var(--color-accent)] hover:underline">
                Domain home
              </Link>
              {data.paths.map((path) => (
                <Link key={path.slug} to={path.href} className="text-[var(--color-accent)] hover:underline">
                  {path.title}
                </Link>
              ))}
              {data.projects.map((project) => (
                <Link key={project.slug} to={project.href} className="text-[var(--color-accent)] hover:underline">
                  {project.title}
                </Link>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
