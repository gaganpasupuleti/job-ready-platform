type SupportQuery = {
  data?: unknown
  isError: boolean
  fetchStatus: string
  error: unknown
}

export function supportLoadFailed(query: SupportQuery) {
  return query.data == null && (query.isError || query.fetchStatus === 'paused')
}

export function supportLoadMessage(error: unknown, fallback: string) {
  if (typeof navigator !== 'undefined' && navigator.onLine === false) {
    return 'Could not reach the server. Check your connection and retry.'
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}
