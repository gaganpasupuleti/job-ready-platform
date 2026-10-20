import { ChevronDown } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/utils/cn'

interface FilterDisclosureProps {
  title: string
  open: boolean
  onOpenChange: (open: boolean) => void
  activeCount?: number
  children: ReactNode
  className?: string
}

export function FilterDisclosure({
  title,
  open,
  onOpenChange,
  activeCount = 0,
  children,
  className,
}: FilterDisclosureProps) {
  return (
    <section className={cn('filter-disclosure', className)}>
      <button
        type="button"
        className="filter-disclosure-trigger"
        aria-expanded={open}
        onClick={() => onOpenChange(!open)}
      >
        <span>{title}</span>
        {activeCount > 0 ? (
          <span className="filter-disclosure-badge" aria-label={`${activeCount} active filters`}>
            {activeCount}
          </span>
        ) : null}
        <ChevronDown className={cn('filter-disclosure-chevron', open && 'is-open')} aria-hidden />
      </button>
      {open ? <div className="filter-disclosure-panel">{children}</div> : null}
    </section>
  )
}
