import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

interface AdminQuestionListItem {
  id: string
  title: string | null
  question_text: string
  difficulty: string
  domain_name: string
  category_name: string
  topic_name: string
  is_active: boolean
  is_sample: boolean
}

export function AdminQuestionsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-questions'],
    queryFn: async () => {
      const { data: response } = await apiClient.get<{ questions: AdminQuestionListItem[]; total: number }>(
        apiEndpoints.admin.questions,
      )
      return response
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[var(--color-text)]">Question Management</h2>
          <p className="text-sm text-[var(--color-text-muted)]">Manage the universal question bank</p>
        </div>
        <Link to="/admin/questions/new">
          <Button variant="primary">New Question</Button>
        </Link>
      </div>

      <Card>
        <CardHeader title={`Questions (${data?.total ?? 0})`} />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-[var(--color-text-subtle)]">
                <tr>
                  <th className="pb-2">Question</th>
                  <th className="pb-2">Taxonomy</th>
                  <th className="pb-2">Difficulty</th>
                  <th className="pb-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {data?.questions.map((question) => (
                  <tr key={question.id} className="border-t border-[var(--color-border)]">
                    <td className="py-3 pr-4">
                      <Link
                        to={`/admin/questions/${question.id}/edit`}
                        className="text-[var(--color-accent)] hover:underline"
                      >
                        {question.title ?? question.question_text.slice(0, 80)}
                      </Link>
                    </td>
                    <td className="py-3 pr-4 text-xs text-[var(--color-text-muted)]">
                      {question.domain_name} / {question.category_name} / {question.topic_name}
                    </td>
                    <td className="py-3 pr-4">{question.difficulty}</td>
                    <td className="py-3">
                      <div className="flex gap-1">
                        <Badge variant={question.is_active ? 'success' : 'warning'}>
                          {question.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                        {question.is_sample && <Badge>Sample</Badge>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
