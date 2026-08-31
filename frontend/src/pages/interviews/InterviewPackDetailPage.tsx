import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
  PracticeHeader,
} from '@/components/practice-workspace/PracticeWorkspace'
import {
  createInterviewSession,
  fetchInterviewPackDetail,
} from '@/services/interviewService'
import type { InterviewSessionMode } from '@/types/interview'

export function InterviewPackDetailPage() {
  const { slug = '' } = useParams()
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery({
    queryKey: ['interview-pack', slug],
    queryFn: () => fetchInterviewPackDetail(slug),
    enabled: Boolean(slug),
  })

  const startMutation = useMutation({
    mutationFn: (mode: InterviewSessionMode) =>
      createInterviewSession({
        mode,
        source_type: 'pack',
        pack_slug: slug,
      }),
    onSuccess: (detail) => navigate(`/interviews/sessions/${detail.session.id}`),
  })

  if (isLoading) return <LoadingState label="Loading pack" />
  if (error || !data) return <ErrorState message="Unable to load this interview pack." />

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/interviews/packs" backLabel="All packs" title={data.title}>
        {data.description && (
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">{data.description}</p>
        )}
      </PracticeHeader>

      <div className="flex flex-wrap gap-2">
        <Badge>{data.question_count} questions</Badge>
        {data.experience_level && <Badge>{data.experience_level}</Badge>}
        {data.target_role && <Badge>{data.target_role}</Badge>}
        {data.target_company && <Badge>{data.target_company}</Badge>}
        {data.estimated_minutes != null && <Badge>~{data.estimated_minutes} min</Badge>}
      </div>

      <Card>
        <CardHeader title="Start practice" description="Choose a mode for this pack" />
        <div className="flex flex-wrap gap-2">
          {data.active_session_id && (
            <Link to={`/interviews/sessions/${data.active_session_id}`}>
              <Button variant="primary">Continue</Button>
            </Link>
          )}
          <Button
            variant="primary"
            disabled={startMutation.isPending}
            onClick={() => startMutation.mutate('study')}
          >
            Start Study
          </Button>
          <Button disabled={startMutation.isPending} onClick={() => startMutation.mutate('mock')}>
            Start Mock
          </Button>
          <Button
            disabled={startMutation.isPending}
            onClick={() => startMutation.mutate('rapid_review')}
          >
            Rapid Review
          </Button>
        </div>
        {startMutation.isError && (
          <p className="mt-3 text-sm text-red-700 dark:text-red-300">Could not start session.</p>
        )}
      </Card>

      {(data.skills_covered.length > 0 || Object.keys(data.difficulty_mix).length > 0) && (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.skills_covered.length > 0 && (
            <Card>
              <CardHeader title="Skills covered" />
              <div className="flex flex-wrap gap-1">
                {data.skills_covered.map((skill) => (
                  <Badge key={skill}>{skill}</Badge>
                ))}
              </div>
            </Card>
          )}
          {Object.keys(data.difficulty_mix).length > 0 && (
            <Card>
              <CardHeader title="Difficulty mix" />
              <ul className="space-y-1 text-sm text-[var(--color-text)]">
                {Object.entries(data.difficulty_mix).map(([level, count]) => (
                  <li key={level}>
                    {level}: {count}
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
