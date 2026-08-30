import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchAdminPrompts } from '@/services/aiService'

export function AdminPromptsPage() {
  const { data, isLoading } = useQuery({ queryKey: ['admin-prompts'], queryFn: fetchAdminPrompts })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Prompt Challenges</h2>
        <Link to="/admin/ai/prompts/new">
          <Button>New challenge</Button>
        </Link>
      </div>
      <Card>
        <CardHeader title={`Challenges (${data?.length ?? 0})`} />
        {isLoading ? (
          <p className="text-sm">Loading...</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-xs text-[var(--color-text-subtle)]">
                <th className="pb-2">Title</th>
                <th className="pb-2">Slug</th>
                <th className="pb-2">Difficulty</th>
                <th className="pb-2">Active</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((row) => (
                <tr key={String(row.id)} className="border-t border-[var(--color-border)]">
                  <td className="py-2">
                    <Link to={`/admin/ai/prompts/${row.id}/edit`} className="text-[var(--color-accent)] hover:underline">
                      {String(row.title)}
                    </Link>
                  </td>
                  <td className="py-2 text-xs">{String(row.slug)}</td>
                  <td className="py-2">
                    <Badge>{String(row.difficulty)}</Badge>
                  </td>
                  <td className="py-2">{row.is_active ? 'yes' : 'no'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
