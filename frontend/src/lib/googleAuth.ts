/** Public Google web client id. Empty means the button stays hidden. */
export function resolveGoogleClientId(
  envValue: string | undefined,
  devOverride?: string | null,
  isDev = false,
): string {
  const fromEnv = (envValue ?? '').trim()
  if (fromEnv) return fromEnv
  if (!isDev) return ''
  return (devOverride ?? '').trim()
}

export function googleClientId(): string {
  const override =
    typeof window !== 'undefined' ? window.__JOBREADY_E2E_GOOGLE_CLIENT_ID : undefined
  return resolveGoogleClientId(import.meta.env.VITE_GOOGLE_CLIENT_ID, override, import.meta.env.DEV)
}

export function googleDestination(isNewUser: boolean, from: string | null): string {
  if (isNewUser) return '/jobs/preferences'
  if (from && from.startsWith('/') && !from.startsWith('//')) return from
  return '/jobs'
}

declare global {
  interface Window {
    __JOBREADY_E2E_GOOGLE_CLIENT_ID?: string
  }
}
