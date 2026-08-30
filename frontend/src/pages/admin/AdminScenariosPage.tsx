import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchAdminScenarios } from '@/services/infraService'

export function AdminScenariosPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-scenarios'],
    queryFn: fetchAdminScenarios,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Scenarios</h2>
        <Link to="/admin/scenarios/new">
          <Button>New scenario</Button>
        </Link>
      </div>
      {isLoading && <p className="text-sm">Loading...</p>}
      <Card>
        <CardHeader title="Bank" />
        <div className="space-y-2 text-sm">
          {(data ?? []).map((row) => (
            <div key={String(row.id)} className="flex justify-between gap-3">
              <span>
                {String(row.title)} · {String(row.domain_key)} · {String(row.difficulty)} ·{' '}
                {row.is_active ? 'active' : 'hidden'}
              </span>
              <Link to={`/admin/scenarios/${row.id}/edit`} className="text-[var(--color-accent)] hover:underline">
                Edit
              </Link>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
