import type { InterviewConfidence, InterviewSelfRating } from '@/types/interview'

const CONFIDENCE_OPTIONS: { value: InterviewConfidence; label: string }[] = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
]

const RATING_OPTIONS: { value: InterviewSelfRating; label: string }[] = [
  { value: 'needs_review', label: 'Needs review' },
  { value: 'partial', label: 'Partial' },
  { value: 'good', label: 'Good' },
  { value: 'strong', label: 'Strong' },
]

export function InterviewReviewForm({
  keyPoints,
  checkedIds,
  confidence,
  selfRating,
  needsReview,
  onToggleKeyPoint,
  onConfidenceChange,
  onSelfRatingChange,
  onNeedsReviewChange,
  disabled,
}: {
  keyPoints: Array<{ id: string; point_text: string }>
  checkedIds: string[]
  confidence: InterviewConfidence | null
  selfRating: InterviewSelfRating | null
  needsReview: boolean
  onToggleKeyPoint: (id: string) => void
  onConfidenceChange: (value: InterviewConfidence) => void
  onSelfRatingChange: (value: InterviewSelfRating) => void
  onNeedsReviewChange: (value: boolean) => void
  disabled?: boolean
}) {
  return (
    <div className="space-y-5">
      {keyPoints.length > 0 && (
        <fieldset disabled={disabled} className="space-y-2">
          <legend className="text-sm font-medium text-[var(--color-text)]">Key points covered</legend>
          <div className="space-y-2">
            {keyPoints.map((point) => {
              const inputId = `key-point-${point.id}`
              return (
                <label
                  key={point.id}
                  htmlFor={inputId}
                  className="flex cursor-pointer items-start gap-2 text-sm text-[var(--color-text)]"
                >
                  <input
                    id={inputId}
                    type="checkbox"
                    className="mt-1"
                    checked={checkedIds.includes(point.id)}
                    onChange={() => onToggleKeyPoint(point.id)}
                  />
                  <span>{point.point_text}</span>
                </label>
              )
            })}
          </div>
        </fieldset>
      )}

      <fieldset disabled={disabled} className="space-y-2">
        <legend className="text-sm font-medium text-[var(--color-text)]">Confidence</legend>
        <div className="flex flex-wrap gap-3">
          {CONFIDENCE_OPTIONS.map((option) => {
            const inputId = `confidence-${option.value}`
            return (
              <label
                key={option.value}
                htmlFor={inputId}
                className="flex cursor-pointer items-center gap-2 text-sm text-[var(--color-text)]"
              >
                <input
                  id={inputId}
                  type="radio"
                  name="interview-confidence"
                  checked={confidence === option.value}
                  onChange={() => onConfidenceChange(option.value)}
                />
                {option.label}
              </label>
            )
          })}
        </div>
      </fieldset>

      <fieldset disabled={disabled} className="space-y-2">
        <legend className="text-sm font-medium text-[var(--color-text)]">Self-rating</legend>
        <div className="flex flex-wrap gap-3">
          {RATING_OPTIONS.map((option) => {
            const inputId = `self-rating-${option.value}`
            return (
              <label
                key={option.value}
                htmlFor={inputId}
                className="flex cursor-pointer items-center gap-2 text-sm text-[var(--color-text)]"
              >
                <input
                  id={inputId}
                  type="radio"
                  name="interview-self-rating"
                  checked={selfRating === option.value}
                  onChange={() => onSelfRatingChange(option.value)}
                />
                {option.label}
              </label>
            )
          })}
        </div>
      </fieldset>

      <label
        htmlFor="needs-review-flag"
        className="flex cursor-pointer items-center gap-2 text-sm text-[var(--color-text)]"
      >
        <input
          id="needs-review-flag"
          type="checkbox"
          checked={needsReview}
          disabled={disabled}
          onChange={(e) => onNeedsReviewChange(e.target.checked)}
        />
        Flag for later review
      </label>
    </div>
  )
}
