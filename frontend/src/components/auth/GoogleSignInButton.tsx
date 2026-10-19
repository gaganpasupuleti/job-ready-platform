import { useEffect, useRef, useState } from 'react'

import { googleClientId } from '@/lib/googleAuth'

type GoogleId = {
  initialize: (config: {
    client_id: string
    callback: (response: { credential?: string }) => void
  }) => void
  renderButton: (parent: HTMLElement, options: Record<string, string | number>) => void
}

declare global {
  interface Window {
    google?: { accounts?: { id?: GoogleId } }
  }
}

async function loadGoogleIdentity(): Promise<GoogleId> {
  const existing = window.google?.accounts?.id
  if (existing) return existing
  await new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Google sign-in failed to load'))
    document.head.appendChild(script)
  })
  const loaded = window.google?.accounts?.id
  if (!loaded) throw new Error('Google sign-in failed to load')
  return loaded
}

export function GoogleSignInButton({
  disabled,
  onCredential,
}: {
  disabled?: boolean
  onCredential: (credential: string) => void
}) {
  const clientId = googleClientId()
  const hostRef = useRef<HTMLDivElement>(null)
  const onCredentialRef = useRef(onCredential)
  const [unavailable, setUnavailable] = useState(false)

  useEffect(() => {
    onCredentialRef.current = onCredential
  }, [onCredential])

  useEffect(() => {
    if (!clientId || !hostRef.current) return
    let cancelled = false
    const host = hostRef.current
    loadGoogleIdentity()
      .then((google) => {
        if (cancelled) return
        google.initialize({
          client_id: clientId,
          callback: (response) => {
            if (response.credential) onCredentialRef.current(response.credential)
          },
        })
        host.replaceChildren()
        google.renderButton(host, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'continue_with',
          shape: 'rectangular',
          width: Math.max(host.offsetWidth, 280),
          logo_alignment: 'left',
        })
      })
      .catch(() => {
        if (!cancelled) setUnavailable(true)
      })
    return () => {
      cancelled = true
    }
  }, [clientId])

  if (!clientId) return null

  return (
    <div className="mb-4 space-y-4">
      {unavailable ? (
        <p className="text-center text-xs text-[var(--color-text-muted)]" role="status">
          Google sign-in is unavailable.
        </p>
      ) : (
        <div
          ref={hostRef}
          className={disabled ? 'pointer-events-none w-full opacity-60' : 'w-full'}
        />
      )}
      <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]" aria-hidden="true">
        <span className="h-px flex-1 bg-[var(--color-border)]" />
        or
        <span className="h-px flex-1 bg-[var(--color-border)]" />
      </div>
    </div>
  )
}
