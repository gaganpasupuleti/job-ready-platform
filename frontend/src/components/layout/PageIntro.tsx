import type { ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface PageIntroProps {
  title: string
  description?: ReactNode
  aside?: ReactNode
  className?: string
}

/** Shared page title — compact size (retro h1 is heavy; avoid oversized titles). */
export function PageIntro({ title, description, aside, className }: PageIntroProps) {
  return (
    <header className={cn('page-intro flex flex-wrap items-start justify-between gap-3', className)}>
      <div className="min-w-0 max-w-3xl">
        <h1 className="page-intro-title">{title}</h1>
        {description ? (
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">{description}</p>
        ) : null}
      </div>
      {aside ? <div className="shrink-0">{aside}</div> : null}
    </header>
  )
}
