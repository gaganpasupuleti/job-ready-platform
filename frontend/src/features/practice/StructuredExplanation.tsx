import { splitExplanation } from '@/lib/structuredExplanation'

interface StructuredExplanationProps {
  text: string
  className?: string
}

export function StructuredExplanation({ text, className }: StructuredExplanationProps) {
  const sections = splitExplanation(text)
  const bodyClass = className ?? 'whitespace-pre-wrap text-sm text-[var(--color-text-muted)]'
  if (sections.length === 1 && sections[0].heading == null) {
    return <p className={bodyClass}>{sections[0].body}</p>
  }
  return (
    <div className="space-y-3">
      {sections.map((section, index) => (
        <section key={`${section.heading ?? 'lead'}-${index}`}>
          {section.heading && (
            <h3 className="text-sm font-semibold text-[var(--color-text)]">{section.heading}</h3>
          )}
          {section.body && <p className={bodyClass}>{section.body}</p>}
        </section>
      ))}
    </div>
  )
}
