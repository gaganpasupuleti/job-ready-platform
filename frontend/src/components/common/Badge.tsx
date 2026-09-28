import type { HTMLAttributes, ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode
  variant?: 'default' | 'accent' | 'success' | 'warning'
  className?: string
}

const variants = {
  default: 'bg-[var(--color-surface-muted)] text-[var(--color-text-muted)]',
  accent: 'bg-[var(--color-accent-muted)] text-[var(--color-accent)]',
  success: 'bg-[#e7efe9] text-[var(--color-success)] dark:bg-[#243028] dark:text-[#c5ddd0]',
  warning: 'bg-[#f3eee4] text-[var(--color-warning)] dark:bg-[#322c22] dark:text-[#e4d3b0]',
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
