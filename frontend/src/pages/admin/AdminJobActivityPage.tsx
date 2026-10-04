import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import { Card, CardHeader } from '@/components/common/Card'
import { ErrorState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'

type StudentActivity = {
  email: string
  full_name: string | null
  jobs_opened: number
  opens: number
  duration_seconds: number
  last_opened_at: string | null
}

type JobActivity = {
  email: string
  full_name: string | null
  job_title: string
  opens: number
  duration_seconds: number
  last_opened_at: string
}

function formatDuration(seconds: number) {
  const total = Math.max(0, seconds)
  const minutes = Math.floor(total / 60)
  const rest = total % 60
  if (minutes === 0) return `${rest}s`
  return `${minutes}m ${rest}s`
}

export function AdminJobActivityPage() {
  const students = useQuery({
    queryKey: ['admin-job-engagement'],
    queryFn: async () => {
      const { data } = await apiClient.get<StudentActivity[]>(apiEndpoints.admin.jobs.engagement)
      return data
    },
  })
  const jobs = useQuery({
    queryKey: ['admin-job-engagement-jobs'],
    queryFn: async () => {
      const { data } = await apiClient.get<JobActivity[]>(apiEndpoints.admin.jobs.engagementJobs)
      return data
    },
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Job activity</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Jobs a student opened, and how long the job page stayed visible.
        </p>
      </div>
      <Card>
        <CardHeader title="Students" />
        {students.isLoading ? <LoadingState label="Loading job activity" /> : null}
        {students.isError ? <ErrorState message="Unable to load job activity." /> : null}
        {students.data && students.data.length === 0 ? (
          <p className="text-sm text-[var(--color-text-muted)]">No job opens yet.</p>
        ) : null}
        {students.data && students.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-[var(--color-text-subtle)]">
                  <th className="py-2 pr-3 font-medium">Student</th>
                  <th className="py-2 pr-3 font-medium">Jobs opened</th>
                  <th className="py-2 pr-3 font-medium">Opens</th>
                  <th className="py-2 pr-3 font-medium">Time</th>
                </tr>
              </thead>
              <tbody>
                {students.data.map((row) => (
                  <tr key={row.email} className="border-t border-[var(--color-border)]">
                    <td className="py-2 pr-3">
                      <div>{row.full_name || row.email}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">{row.email}</div>
                    </td>
                    <td className="py-2 pr-3">{row.jobs_opened}</td>
                    <td className="py-2 pr-3">{row.opens}</td>
                    <td className="py-2 pr-3">{formatDuration(row.duration_seconds)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </Card>
      <Card>
        <CardHeader title="Recent jobs" />
        {jobs.isLoading ? <LoadingState label="Loading recent jobs" /> : null}
        {jobs.isError ? <ErrorState message="Unable to load recent jobs." /> : null}
        {jobs.data && jobs.data.length === 0 ? (
          <p className="text-sm text-[var(--color-text-muted)]">No job opens yet.</p>
        ) : null}
        {jobs.data && jobs.data.length > 0 ? (
          <ul className="space-y-2 text-sm">
            {jobs.data.slice(0, 50).map((row) => (
              <li key={`${row.email}-${row.job_title}-${row.last_opened_at}`} className="border-t border-[var(--color-border)] pt-2">
                <span className="font-medium">{row.full_name || row.email}</span>
                {' opened '}
                {row.job_title}
                {' · '}
                {row.opens} {row.opens === 1 ? 'open' : 'opens'}
                {' · '}
                {formatDuration(row.duration_seconds)}
              </li>
            ))}
          </ul>
        ) : null}
      </Card>
    </div>
  )
}
