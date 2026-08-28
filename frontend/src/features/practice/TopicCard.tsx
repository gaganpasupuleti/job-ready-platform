import { cn } from '@/utils/cn'

interface TopicCardProps {
  name: string
  selected?: boolean
  onSelect: () => void
}

export function TopicCard({ name, selected, onSelect }: TopicCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        'rounded-md border px-3 py-2 text-left text-sm transition-colors',
        selected
          ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
          : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-muted)]',
      )}
    >
      {name}
    </button>
  )
}
