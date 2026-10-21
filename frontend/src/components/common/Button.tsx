import type { ButtonHTMLAttributes, ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md'
  children: ReactNode
}

const sizes = {
  sm: 'jr-btn--sm',
  md: 'jr-btn--md',
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
      type="button"
      data-variant={variant}
      className={cn('jr-btn', sizes[size], className)}
      {...props}
    >
      {children}
    </button>
  )
}
