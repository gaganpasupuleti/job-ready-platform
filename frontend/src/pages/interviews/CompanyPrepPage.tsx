import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PracticeHeader,
} from '@/components/practice-workspace/PracticeWorkspace'
import { fetchCompanyPrepList } from '@/services/interviewService'

export function CompanyPrepPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['company-prep'],
    queryFn: fetchCompanyPrepList,
  })

  return (
    <div className="space-y-6">
      <PracticeHeader backTo="/interviews" backLabel="Interview hub" title="Company prep">
        <p className="text-sm text-[var(--color-text-muted)]">
          Practice packs organized by company. These are study guides — not insider interview leaks.
        </p>
      </PracticeHeader>

      <Card padding="sm" className="border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950">
        <p className="text-sm text-amber-900 dark:text-amber-100">
          Disclaimer: Company prep content is curated practice material. It does not guarantee interview
          questions, hiring outcomes, or official company processes.
        </p>
      </Card>

      {isLoading && <LoadingState label="Loading companies" />}
      {error && <ErrorState message="Unable to load company prep." />}

      {!isLoading && !error && (
        <>
          {data?.length ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {data.map((company) => (
                <Link
                  key={company.slug}
                  to={`/company-prep/${company.slug}`}
                  className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 hover:border-[var(--color-accent)]"
                >
                  <p className="font-medium text-[var(--color-text)]">{company.name}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    <Badge>{company.interview_pack_count} packs</Badge>
                    {company.practice_path_slugs.length > 0 && (
                      <Badge>{company.practice_path_slugs.length} paths</Badge>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState title="No companies listed" description="Company prep cards will appear after seeding." />
          )}
        </>
      )}
    </div>
  )
}
