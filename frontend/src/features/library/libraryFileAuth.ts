export function libraryFileNeedsBearer(url: string) {
  if (url.startsWith('/api/')) return true
  if (typeof window === 'undefined') return false
  try {
    const parsed = new URL(url, window.location.href)
    return (
      parsed.origin === window.location.origin &&
      parsed.pathname.startsWith('/api/v1/library/books/') &&
      parsed.pathname.endsWith('/file')
    )
  } catch {
    return false
  }
}
