import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Card, CardHeader } from '@/components/common/Card'
import { LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { fetchSkillProfile } from '@/services/readinessService'

export function ReadinessSkillsPage() {
  const { data, isLoading } = useQuery({ queryKey: ['readiness-skills'], queryFn: fetchSkillProfile })

  if (isLoading) return <LoadingState label="Loading skills" />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-[var(--color-text)]">Skill Profile</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          All skills with recorded evidence from practice, projects, and interview self-review.
        </p>
        <Link to="/readiness" className="mt-2 inline-block text-sm text-[var(--color-accent)] hover:underline">
          Back to readiness
        </Link>
      </div>
      <Card>
        <CardHeader title="Skills" />
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-[var(--color-text-muted)]">
                <th className="py-2 pr-4">Skill</th>
                <th className="py-2 pr-4">Readiness</th>
                <th className="py-2 pr-4">Evidence</th>
                <th className="py-2 pr-4">Activity</th>
                <th className="py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {(data ?? []).map((row: {
                skill: string
                score: number
                evidence_strength: string
                activity_count: number
                status: string
              }) => (
                <tr key={row.skill} className="border-b border-[var(--color-border)]">
                  <td className="py-2 pr-4 font-medium">{row.skill}</td>
                  <td className="py-2 pr-4">{Math.round(row.score)}%</td>
                  <td className="py-2 pr-4 capitalize">{row.evidence_strength}</td>
                  <td className="py-2 pr-4">{row.activity_count}</td>
                  <td className="py-2 capitalize">{row.status.replace('_', ' ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
