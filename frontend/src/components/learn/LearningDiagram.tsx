import { useEffect, useRef, useState } from 'react'

import { Button } from '@/components/common/Button'
import { LearningImage } from '@/components/learn/LearningImage'
import { approvedLearningImageSrc } from '@/lib/learningVisuals'

export function LearningDiagram({
  src,
  alt,
  caption,
}: {
  src: string
  alt: string
  caption?: string | null
}) {
  const approved = approvedLearningImageSrc(src)
  const dialogRef = useRef<HTMLDialogElement>(null)
  const [failed, setFailed] = useState(false)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    if (!expanded) return
    const dialog = dialogRef.current
    if (dialog && !dialog.open) dialog.showModal()
  }, [expanded])

  if (!approved) return <>{alt}</>

  return (
    <figure className="learn-visual">
      <LearningImage
        src={approved}
        alt={alt}
        onStatus={(status) => {
          if (status === 'error') setFailed(true)
        }}
      />
      {caption ? <figcaption>{caption}</figcaption> : null}
      {failed ? null : (
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="mt-2"
          onClick={() => setExpanded(true)}
        >
          View larger
        </Button>
      )}
      <dialog
        ref={dialogRef}
        aria-label={caption || alt}
        className="learn-visual-dialog"
        onClose={() => setExpanded(false)}
      >
        {expanded ? (
          <>
            <LearningImage src={approved} alt={alt} />
            {caption ? <p className="learn-visual-dialog-caption">{caption}</p> : null}
            <Button type="button" variant="secondary" size="sm" className="mt-3" onClick={() => dialogRef.current?.close()}>
              Close
            </Button>
          </>
        ) : null}
      </dialog>
    </figure>
  )
}
