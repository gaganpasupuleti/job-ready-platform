import { Link } from 'react-router-dom'

import { relatedLessonLink, splitExplanation } from '@/lib/structuredExplanation'

interface StructuredExplanationProps {
  text: string
  className?: string
}

export function StructuredExplanation({ text, className }: StructuredExplanationProps) {
  const sections = splitExplanation(text)
  const bodyClass =
    className ?? 'whitespace-pre-wrap break-words text-sm leading-6 text-[var(--color-text-muted)]'
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
          {section.heading === 'Related lesson' && relatedLessonLink(section.body) ? (
            <RelatedLesson body={section.body} className={bodyClass} />
          ) : (
            section.body && <p className={bodyClass}>{section.body}</p>
          )}
        </section>
      ))}
    </div>
  )
}

function RelatedLesson({ body, className }: { body: string; className: string }) {
  const related = relatedLessonLink(body)
  if (!related) return <p className={className}>{body}</p>
  return (
    <p className={className}>
      <Link to={related.href} className="font-medium break-words text-[var(--color-accent)] underline">
        {related.title}
      </Link>
      {related.note ? ` ${related.note}` : ''}
    </p>
  )
}
