import type { ButtonHTMLAttributes, ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md'
  children: ReactNode
}

const variants = {
  primary:
    'bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)] border border-transparent',
  secondary:
    'bg-[var(--color-surface-elevated)] text-[var(--color-text)] border border-[var(--color-border)] hover:bg-[var(--color-surface-muted)]',
  ghost:
    'bg-transparent text-[var(--color-text-muted)] border border-transparent hover:bg-[var(--color-surface-muted)] hover:text-[var(--color-text)]',
}

const sizes = {
  sm: 'h-7 px-2.5 text-xs',
  md: 'h-8 px-3 text-sm',
}

export function Button({
  variant = 'secondary',
  size = 'md',
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-1.5 rounded-[var(--radius-control)] font-medium transition-colors disabled:opacity-50',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
