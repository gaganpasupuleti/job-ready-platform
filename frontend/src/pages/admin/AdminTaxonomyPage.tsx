import { useQuery } from '@tanstack/react-query'

import { Card, CardHeader } from '@/components/common/Card'
import { fetchCatalog } from '@/services/practiceService'

export function AdminTaxonomyPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-taxonomy-view'],
    queryFn: fetchCatalog,
  })

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-[var(--color-text)]">Taxonomy</h2>
      <Card>
        <CardHeader title="Domain → Category → Topic hierarchy" />
        {isLoading ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        ) : (
          <div className="space-y-4 text-sm">
            {data?.domains.map((domain) => (
              <div key={domain.id}>
                <p className="font-medium text-[var(--color-text)]">{domain.name}</p>
                {domain.categories.map((category) => (
                  <div key={category.id} className="ml-4 mt-2">
                    <p className="text-[var(--color-text-muted)]">{category.name}</p>
                    <ul className="ml-4 list-disc text-[var(--color-text-subtle)]">
                      {category.topics.map((topic) => (
                        <li key={topic.id}>{topic.name}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
