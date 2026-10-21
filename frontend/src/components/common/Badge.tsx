import type { HTMLAttributes, ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode
  variant?: 'default' | 'accent' | 'success' | 'warning'
  className?: string
}

const variants = {
  default:
    'border border-[var(--color-border)] bg-[var(--color-surface-muted)] text-[var(--color-text-muted)]',
  accent: 'border border-transparent bg-[var(--color-accent-muted)] text-[var(--color-accent)]',
  success: 'border border-[var(--color-border)] bg-[var(--color-surface-muted)] text-[var(--color-success)]',
  warning: 'border border-[var(--color-border)] bg-[var(--color-surface-muted)] text-[var(--color-warning)]',
}

export function Badge({ children, variant = 'default', className, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-[var(--radius-control)] px-1.5 py-0.5 text-[11px] font-medium leading-4',
        variants[variant],
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  )
}
