import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import { continuationAction, humanLabel, sharedDestinationNote } from '@/lib/studentLabels'
import { fetchInfraHome } from '@/services/infraService'

const COPY: Record<string, { title: string; blurb: string }> = {
  cloud: {
    title: 'Cloud Practice',
    blurb: 'AWS, Azure, GCP, architecture, and cloud security MCQs. No cloud account required.',
  },
  devops: {
    title: 'DevOps Practice',
    blurb: 'Linux, Git, Docker, Kubernetes, CI/CD, Terraform, and SRE — concepts only, no live cluster.',
  },
  cybersecurity: {
    title: 'Cybersecurity Practice',
    blurb: 'Defensive fundamentals, SOC, IAM, web/API security, and incident response. No offensive labs.',
  },
}

export function InfraHomePage({ domain }: { domain: 'cloud' | 'devops' | 'cybersecurity' }) {
  const { data, isLoading } = useQuery({
    queryKey: ['infra-home', domain],
    queryFn: () => fetchInfraHome(domain),
  })
  const copy = COPY[domain]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">{copy.title}</h2>
        <p className="text-sm text-[var(--color-text-muted)]">{copy.blurb}</p>
        {data?.unofficial_disclaimer && (
          <p className="mt-1 text-xs text-[var(--color-text-subtle)]">{data.unofficial_disclaimer}</p>
        )}
      </div>
      {isLoading && <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>}
      {data && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.tracks.map((track) => {
              const shared = sharedDestinationNote(track.href, data.tracks.map((item) => item.href))
              return (
                <Link
                  key={track.key}
                  to={track.href}
                  className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 hover:border-[var(--color-accent)]"
                >
                  <h3 className="font-medium text-[var(--color-text)]">{track.label}</h3>
                  <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                    Questions and scenarios for {track.label}. This page does not open a live cloud or cluster.
                  </p>
                  {shared ? <p className="mt-2 text-xs text-[var(--color-text-subtle)]">{shared}</p> : null}
                </Link>
              )
            })}
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader title="Where to go next" />
              {data.continue ? (
                <Link to={data.continue} className="text-sm text-[var(--color-accent)] hover:underline">
                  {continuationAction({ href: data.continue, progress_percent: 1 }).label} this track
                </Link>
              ) : (
                <p className="text-sm text-[var(--color-text-muted)]">No saved place yet. Open a track or a scenario.</p>
              )}
              <p className="mt-3 text-xs text-[var(--color-text-subtle)]">
                Scenarios attempted {data.progress.scenario_attempted} · mastered {data.progress.scenario_mastered}
              </p>
            </Card>
            <Card>
              <CardHeader title="Weak topics" />
              {data.weak_topics.length ? (
                <ul className="list-disc pl-5 text-sm">
                  {data.weak_topics.map((topic) => (
                    <li key={topic}>{topic}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-[var(--color-text-muted)]">Complete MCQ sessions to see weak topics.</p>
              )}
            </Card>
          </div>
          <Card>
            <CardHeader title="Scenarios" />
            <div className="space-y-2">
              {data.scenarios.map((row) => (
                <Link key={row.slug} to={`/scenarios/${row.slug}`} className="block text-sm hover:underline">
                  {row.title}{' '}
                  <span className="text-[var(--color-text-muted)]">
                    {humanLabel(row.difficulty)}
                    {row.status ? ` · best ${row.best_score}` : ' · no attempt yet'}
                  </span>
                </Link>
              ))}
            </div>
            <Link to={`/${domain}/progress`} className="mt-3 inline-block text-sm text-[var(--color-accent)] hover:underline">
              Progress
            </Link>
          </Card>
          <Card>
            <CardHeader title="Paths and projects" />
            <div className="flex flex-wrap gap-2">
              {data.paths.map((path) => (
                <Link key={path.slug} to={path.href}>
                  <Badge>{path.title}</Badge>
                </Link>
              ))}
              {data.projects.map((project) => (
                <Link key={project.slug} to={project.href}>
                  <Badge>{project.title}</Badge>
                </Link>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
