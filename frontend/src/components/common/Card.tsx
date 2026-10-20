import type { ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface CardProps {
  children: ReactNode
  className?: string
  padding?: 'sm' | 'md' | 'lg'
}

const paddingMap = {
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-5',
}

export function Card({ children, className, padding = 'md' }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-[var(--jr-radius,2px)] border-2 border-[var(--jr-ink,#0a0a0a)] bg-[var(--jr-surface,#fffef8)] shadow-[2px_2px_0_#0a0a0a]',
        paddingMap[padding],
        className,
      )}
    >
      {children}
    </div>
  )
}

interface CardHeaderProps {
  title: string
  description?: string
  action?: ReactNode
}

export function CardHeader({ title, description, action }: CardHeaderProps) {
  return (
    <div className="mb-4 flex min-w-0 items-start justify-between gap-3">
      <div className="min-w-0">
        <h3 className="text-sm font-extrabold text-[var(--color-text)]">{title}</h3>
        {description && (
          <p className="mt-1 break-words text-xs text-[var(--color-text-muted)]">{description}</p>
        )}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  )
}
