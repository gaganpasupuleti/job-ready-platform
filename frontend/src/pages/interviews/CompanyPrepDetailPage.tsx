import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
  PracticeHeader,
} from '@/components/practice-workspace/PracticeWorkspace'
import { InterviewPackCard } from '@/features/interviews/InterviewPackCard'
import { fetchCompanyPrepDetail } from '@/services/interviewService'

export function CompanyPrepDetailPage() {
  const { slug = '' } = useParams()
  const { data, isLoading, error } = useQuery({
    queryKey: ['company-prep', slug],
    queryFn: () => fetchCompanyPrepDetail(slug),
    enabled: Boolean(slug),
  })

  if (isLoading) return <LoadingState label="Loading company prep" />
  if (error || !data) return <ErrorState message="Unable to load this company prep page." />

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/company-prep" backLabel="Companies" title={data.name} />

      <Card padding="sm" className="border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950">
        <p className="text-sm text-amber-900 dark:text-amber-100">{data.disclaimer}</p>
      </Card>

      {data.skills.length > 0 && (
        <Card>
          <CardHeader title="Focus skills" />
          <div className="flex flex-wrap gap-1">
            {data.skills.map((skill) => (
              <Badge key={skill}>{skill}</Badge>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <CardHeader title="Interview packs" />
        {data.packs.length ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {data.packs.map((pack) => (
              <InterviewPackCard key={pack.id} pack={pack} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-[var(--color-text-muted)]">No packs linked yet.</p>
        )}
      </Card>

      {data.practice_paths.length > 0 && (
        <Card>
          <CardHeader title="Related practice paths" />
          <ul className="space-y-2 text-sm">
            {data.practice_paths.map((path, index) => {
              const title = typeof path.title === 'string' ? path.title : path.slug ?? `Path ${index + 1}`
              const href =
                typeof path.href === 'string'
                  ? path.href
                  : path.slug
                    ? `/practice/paths/${path.slug}`
                    : null
              return (
                <li key={href ?? String(index)}>
                  {href ? (
                    <Link to={href} className="text-[var(--color-accent)] hover:underline">
                      {title}
                    </Link>
                  ) : (
                    <span className="text-[var(--color-text)]">{title}</span>
                  )}
                </li>
              )
            })}
          </ul>
        </Card>
      )}
    </div>
  )
}
