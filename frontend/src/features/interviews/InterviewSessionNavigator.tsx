import { cn } from '@/utils/cn'
import type { InterviewNavigatorItem } from '@/types/interview'

export function InterviewSessionNavigator({
  items,
  onSelect,
}: {
  items: InterviewNavigatorItem[]
  onSelect: (number: number) => void
}) {
  return (
    <div className="flex flex-wrap gap-2" role="navigation" aria-label="Question navigator">
      {items.map((item) => {
        const variant =
          item.status === 'reviewed' || item.status === 'completed'
            ? 'reviewed'
            : item.status === 'viewed'
              ? 'viewed'
              : 'unseen'
        return (
          <button
            key={item.number}
            type="button"
            onClick={() => onSelect(item.number)}
            aria-current={item.current ? 'true' : undefined}
            aria-label={`Question ${item.number}${item.needs_review ? ', needs review' : ''}`}
            className={cn(
              'flex h-9 w-9 items-center justify-center rounded-md border text-xs font-medium',
              item.current
                ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                : variant === 'reviewed'
                  ? 'border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200'
                  : variant === 'viewed'
                    ? 'border-[var(--color-border)] bg-[var(--color-surface-muted)] text-[var(--color-text)]'
                    : 'border-[var(--color-border)] text-[var(--color-text-muted)]',
              item.needs_review && !item.current && 'ring-1 ring-amber-400',
            )}
          >
            {item.number}
          </button>
        )
      })}
    </div>
  )
}
