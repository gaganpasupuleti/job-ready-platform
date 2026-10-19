/** Reader view rules. Opening a PDF does not write progress or complete a book. */

export function initialReaderPage(lastPage: number | null, pageCount: number) {
  if (!lastPage || lastPage < 1 || pageCount < 1) return 1
  return Math.min(lastPage, pageCount)
}

export function progressWrite(savedPage: number | null, nextPage: number, fromUser: boolean) {
  if (!fromUser || nextPage < 1) return null
  if (savedPage === nextPage) return null
  return nextPage
}

export function shouldRefreshReadLink(status: number, alreadyRetried: boolean) {
  return !alreadyRetried && status === 403
}

export function readerFileUrl(available: boolean, hasFile: boolean, fileUrl: string | null) {
  if (!available || !hasFile) return null
  return fileUrl
}
