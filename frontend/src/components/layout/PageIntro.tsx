import type { ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface PageIntroProps {
  title: string
  /** Title already shown in app subheader — omit duplicate h1. */
  titleInSubheader?: boolean
  description?: ReactNode
  aside?: ReactNode
  className?: string
}

/** Shared page title — compact size (retro h1 is heavy; avoid oversized titles). */
export function PageIntro({
  title,
  titleInSubheader = false,
  description,
  aside,
  className,
}: PageIntroProps) {
  return (
    <header className={cn('page-intro flex flex-wrap items-start justify-between gap-3', className)}>
      <div className="min-w-0 max-w-3xl">
        {titleInSubheader ? (
          <p className="sr-only">{title}</p>
        ) : (
          <h1 className="page-intro-title">{title}</h1>
        )}
        {description ? (
          <p className={cn('text-sm text-[var(--color-text-muted)]', !titleInSubheader && 'mt-1')}>
            {description}
          </p>
        ) : null}
      </div>
      {aside ? <div className="shrink-0">{aside}</div> : null}
    </header>
  )
}
