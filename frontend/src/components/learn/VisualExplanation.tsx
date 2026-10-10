import type { ReactNode } from 'react'

import { LearningDiagram } from '@/components/learn/LearningDiagram'

/** Concept text plus one reviewed diagram. Lesson Markdown uses this for image tokens. */
export function VisualExplanation({
  title,
  children,
  src,
  alt,
  caption,
}: {
  title?: string
  children?: ReactNode
  src: string
  alt: string
  caption?: string | null
}) {
  return (
    <div className="learn-visual-explanation">
      {title ? <h3 className="learn-md-heading">{title}</h3> : null}
      {children ? <div className="learn-visual-copy">{children}</div> : null}
      <LearningDiagram src={src} alt={alt} caption={caption} />
    </div>
  )
}
