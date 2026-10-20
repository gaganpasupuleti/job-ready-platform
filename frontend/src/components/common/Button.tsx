import type { ButtonHTMLAttributes, ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md'
  children: ReactNode
}

const variants = {
  primary:
    'bg-[var(--jr-line,#2b78e4)] text-white border-2 border-[var(--jr-ink,#0a0a0a)] shadow-[2px_2px_0_#0a0a0a] hover:bg-[var(--jr-accent,#1d4ed8)] hover:translate-x-[-1px] hover:translate-y-[-1px] hover:shadow-[3px_3px_0_#0a0a0a]',
  secondary:
    'bg-[var(--jr-surface,#fffef8)] text-[var(--jr-ink,#0a0a0a)] border-2 border-[var(--jr-ink,#0a0a0a)] shadow-[2px_2px_0_#0a0a0a] hover:bg-[var(--jr-milestone,#fff200)] hover:translate-x-[-1px] hover:translate-y-[-1px] hover:shadow-[3px_3px_0_#0a0a0a]',
  ghost:
    'bg-transparent text-[var(--color-text-muted)] border-2 border-transparent hover:border-[var(--jr-ink,#0a0a0a)] hover:bg-[var(--jr-peach,#ffdba8)] hover:text-[var(--jr-ink,#0a0a0a)]',
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
        'jr-retro-btn inline-flex items-center justify-center gap-1.5 rounded-[var(--jr-radius,2px)] font-bold transition-[background,transform,box-shadow] disabled:pointer-events-none disabled:cursor-not-allowed disabled:border-[var(--color-border)] disabled:bg-[var(--color-surface-muted)] disabled:text-[var(--color-text-subtle)] disabled:opacity-100 disabled:shadow-none disabled:translate-none',
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
