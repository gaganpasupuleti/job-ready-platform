import { Link } from 'react-router-dom'

import { Card } from '@/components/common/Card'

export function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <Card className="max-w-md text-center" padding="lg">
        <p className="text-sm font-medium text-[var(--color-text-muted)]">404</p>
        <h1 className="mt-2 text-xl font-semibold text-[var(--color-text)]">Page not found</h1>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          This route does not exist or may have moved.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link
            to="/"
            className="inline-flex h-9 items-center rounded-md bg-[var(--color-accent)] px-4 text-sm font-medium text-white"
          >
            Dashboard
          </Link>
          <Link
            to="/practice"
            className="inline-flex h-9 items-center rounded-md border border-[var(--color-border)] px-4 text-sm font-medium text-[var(--color-text)]"
          >
            Practice Hub
          </Link>
        </div>
      </Card>
    </div>
  )
}
