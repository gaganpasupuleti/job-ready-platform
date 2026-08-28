import { cn } from '@/utils/cn'

interface QuestionOptionProps {
  id: string
  text: string
  selected: boolean
  disabled?: boolean
  variant?: 'default' | 'correct' | 'incorrect'
  onSelect: () => void
}

export function QuestionOption({
  text,
  selected,
  disabled,
  variant = 'default',
  onSelect,
}: QuestionOptionProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onSelect}
      className={cn(
        'w-full rounded-md border px-3 py-2 text-left text-sm transition-colors disabled:opacity-70',
        variant === 'correct' && 'border-[var(--color-success)] bg-emerald-50 dark:bg-emerald-950',
        variant === 'incorrect' && 'border-[var(--color-danger)] bg-red-50 dark:bg-red-950',
        variant === 'default' &&
          (selected
            ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)]'
            : 'border-[var(--color-border)] hover:bg-[var(--color-surface-muted)]'),
      )}
    >
      {text}
    </button>
  )
}
