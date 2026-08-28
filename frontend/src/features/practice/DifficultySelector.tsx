import type { Difficulty } from '@/types/practice'

interface DifficultySelectorProps {
  value?: Difficulty
  onChange: (value: Difficulty | undefined) => void
}

const options: Array<{ label: string; value: Difficulty | undefined }> = [
  { label: 'Any', value: undefined },
  { label: 'Easy', value: 'easy' },
  { label: 'Medium', value: 'medium' },
  { label: 'Hard', value: 'hard' },
]

export function DifficultySelector({ value, onChange }: DifficultySelectorProps) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]">
        Difficulty
      </label>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option.label}
            type="button"
            onClick={() => onChange(option.value)}
            className={`rounded-md border px-3 py-1.5 text-xs ${
              value === option.value
                ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                : 'border-[var(--color-border)] text-[var(--color-text-muted)]'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}
