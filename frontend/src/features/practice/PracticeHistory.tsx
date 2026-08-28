import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Card, CardHeader } from '@/components/common/Card'
import { fetchHistory } from '@/services/practiceService'

export function PracticeHistory() {
  const { data } = useQuery({
    queryKey: ['practice-history'],
    queryFn: fetchHistory,
  })

  if (!data?.sessions.length) return null

  return (
    <Card>
      <CardHeader title="Recent Practice" description="Your previous sessions" />
      <ul className="divide-y divide-[var(--color-border)]">
        {data.sessions.slice(0, 5).map((session) => (
          <li key={session.id} className="flex items-center justify-between py-3 text-sm">
            <div>
              <p className="font-medium text-[var(--color-text)]">
                {session.topic_name ?? session.category_name ?? 'Practice Session'}
              </p>
              <p className="text-xs text-[var(--color-text-muted)]">
                {session.mode} · {session.correct_count}/{session.question_count} correct
              </p>
            </div>
            <Link
              to={`/practice/sessions/${session.id}/results`}
              className="text-xs text-[var(--color-accent)] hover:underline"
            >
              View
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  )
}
