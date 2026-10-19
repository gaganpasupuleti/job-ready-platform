type NotificationQuery = {
  data?: unknown
  isError: boolean
  fetchStatus: string
  error: unknown
}

export function notificationLoadFailed(query: NotificationQuery) {
  return query.data == null && (query.isError || query.fetchStatus === 'paused')
}

export function notificationLoadMessage(error: unknown, fallback: string) {
  if (typeof navigator !== 'undefined' && navigator.onLine === false) {
    return 'Could not reach the server. Check your connection and retry.'
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}

export function notificationRefreshMessage(query: NotificationQuery) {
  if (query.data == null) return null
  const offline = typeof navigator !== 'undefined' && navigator.onLine === false
  if (offline && (query.isError || query.fetchStatus === 'paused')) {
    return 'Could not reach the server. Check your connection and retry.'
  }
  if (query.isError) return notificationLoadMessage(query.error, 'Could not refresh notifications.')
  return null
}
