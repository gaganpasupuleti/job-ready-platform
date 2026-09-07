import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp } from 'lucide-react'

import { cn } from '@/utils/cn'

interface SqlPaneResizeHandleProps {
  direction: 'horizontal' | 'vertical'
  onMouseDown: (event: React.MouseEvent) => void
}

export function SqlPaneResizeHandle({ direction, onMouseDown }: SqlPaneResizeHandleProps) {
  return (
    <button
      type="button"
      aria-label={direction === 'horizontal' ? 'Resize side panel' : 'Resize results panel'}
      className={cn(
        'shrink-0 bg-[var(--color-border)] transition-colors hover:bg-[var(--color-accent)]',
        direction === 'horizontal' ? 'w-1 cursor-col-resize' : 'h-1 w-full cursor-row-resize',
      )}
      onMouseDown={onMouseDown}
    />
  )
}

interface SqlExpandRailProps {
  side: 'left' | 'right' | 'bottom'
  label: string
  onExpand: () => void
}

export function SqlExpandRail({ side, label, onExpand }: SqlExpandRailProps) {
  const Icon = side === 'left' ? ChevronRight : side === 'right' ? ChevronLeft : ChevronUp
  return (
    <button
      type="button"
      onClick={onExpand}
      aria-label={`Expand ${label}`}
      title={`Expand ${label}`}
      className={cn(
        'flex shrink-0 items-center justify-center border-[var(--color-border)] bg-[var(--color-surface-muted)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] hover:text-[var(--color-accent)]',
        side === 'bottom' ? 'h-7 w-full border-t' : 'w-7 border-y-0',
        side === 'left' && 'border-r',
        side === 'right' && 'border-l',
      )}
    >
      <Icon className="h-4 w-4" />
    </button>
  )
}

interface SqlPaneCollapseButtonProps {
  side: 'left' | 'right' | 'bottom'
  onClick: () => void
  label: string
}

export function SqlPaneCollapseButton({ side, onClick, label }: SqlPaneCollapseButtonProps) {
  const Icon = side === 'left' ? ChevronLeft : side === 'right' ? ChevronRight : ChevronDown
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Collapse ${label}`}
      title={`Collapse ${label}`}
      className="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-muted)] hover:text-[var(--color-text)]"
    >
      <Icon className="h-3.5 w-3.5" />
    </button>
  )
}
