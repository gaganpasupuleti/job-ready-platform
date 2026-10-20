import type { HTMLAttributes, ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode
  variant?: 'default' | 'accent' | 'success' | 'warning'
  className?: string
}

const variants = {
  default: 'border border-[var(--jr-ink,#0a0a0a)] bg-[var(--jr-peach,#ffdba8)] text-[var(--jr-ink,#0a0a0a)]',
  accent: 'border border-[var(--jr-ink,#0a0a0a)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]',
  success:
    'border border-[var(--jr-ink,#0a0a0a)] bg-[var(--jr-milestone,#fff200)] text-[var(--jr-ink,#0a0a0a)] font-bold',
  warning: 'bg-[#f3eee4] text-[var(--color-warning)] dark:bg-[#322c22] dark:text-[#e4d3b0]',
}

export function Badge({ children, variant = 'default', className, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-[var(--jr-radius,2px)] px-1.5 py-0.5 text-[11px] font-semibold leading-4',
        variants[variant],
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  )
}
