import { useState } from 'react'

import { cn } from '@/utils/cn'

export function LearningImage({
  src,
  alt,
  onStatus,
}: {
  src: string
  alt: string
  onStatus?: (status: 'loading' | 'ready' | 'error') => void
}) {
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')

  function update(next: 'loading' | 'ready' | 'error') {
    setStatus(next)
    onStatus?.(next)
  }

  if (status === 'error') {
    return (
      <p className="learn-visual-fallback" role="status">
        Diagram unavailable. {alt}
      </p>
    )
  }

  return (
    <>
      {status === 'loading' ? (
        <p className="learn-visual-status" role="status">
          Loading diagram
        </p>
      ) : null}
      <img
        src={src}
        alt={alt}
        className={cn('learn-visual-img', status === 'loading' && 'learn-visual-img-loading')}
        onLoad={() => update('ready')}
        onError={() => update('error')}
      />
    </>
  )
}
