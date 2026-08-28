import type { ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'accent' | 'success' | 'warning'
  className?: string
}

const variants = {
  default: 'bg-[var(--color-surface-muted)] text-[var(--color-text-muted)]',
  accent: 'bg-[var(--color-accent-muted)] text-[var(--color-accent)]',
  success: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300',
  warning: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}
