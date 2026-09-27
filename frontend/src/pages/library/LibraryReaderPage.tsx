import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpen, ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { EmptyState, ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { acceptStudentBook, loadLibraryBook } from '@/features/library/libraryQueries'
import { initialReaderPage, progressWrite, readerFileUrl, shouldRefreshReadLink } from '@/features/library/readerModel'
import { useAuth } from '@/hooks/useAuth'
import { fetchLibraryFile, fetchReadLink, LibraryFileError, saveReadingProgress, setReadingStatus, type ReadingStatus, type StudentBook } from '@/services/libraryService'

const STATUSES: { value: ReadingStatus; label: string }[] = [
  { value: 'not_started', label: 'Not started' },
  { value: 'reading', label: 'Reading' },
  { value: 'completed', label: 'Completed' },
]

export function LibraryReaderPage() {
  const { bookId = '' } = useParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [page, setPage] = useState(1)
  const [pageCount, setPageCount] = useState(0)
  const [fileError, setFileError] = useState<string | null>(null)
  const [rendering, setRendering] = useState(false)
  const [linkAttempt, setLinkAttempt] = useState(0)
  const userId = user?.id ?? ''

  const bookQuery = useQuery({
    queryKey: ['library-book', user?.id, bookId],
    queryFn: () => loadLibraryBook(userId, bookId),
    enabled: Boolean(user?.id && bookId),
    retry: false,
  })
  const book = bookQuery.data
  const canRead = Boolean(book?.available && book.has_file)
  const linkQuery = useQuery({
    queryKey: ['library-read-link', user?.id, bookId],
    queryFn: async () => {
      const link = await fetchReadLink(bookId)
      const current = queryClient.getQueryData<StudentBook>(['library-book', user?.id, bookId])
      if (current && !current.available) throw new Error('This resource is not available.')
      return link
    },
    enabled: Boolean(user?.id && canRead),
    retry: false,
  })
  const fileUrl = readerFileUrl(Boolean(book?.available), Boolean(book?.has_file), linkQuery.data?.url ?? null)
  const fileQuery = useQuery({
    queryKey: ['library-file', user?.id, bookId, fileUrl],
    queryFn: async () => {
      const current = queryClient.getQueryData<StudentBook>(['library-book', user?.id, bookId])
      if (!current?.available) throw new Error('This resource is not available.')
      const bytes = await fetchLibraryFile(fileUrl ?? '')
      const after = queryClient.getQueryData<StudentBook>(['library-book', user?.id, bookId])
      if (!after?.available) throw new Error('This resource is not available.')
      return bytes
    },
    enabled: Boolean(fileUrl),
    retry: false,
    structuralSharing: false,
  })

  const fileStatus = fileQuery.error instanceof LibraryFileError ? fileQuery.error.status : 0
  const refreshingLink = shouldRefreshReadLink(fileStatus, linkAttempt > 0)

  useEffect(() => {
    setLinkAttempt(0)
  }, [bookId])

  useEffect(() => {
    if (!refreshingLink) return
    setLinkAttempt(1)
    void queryClient.invalidateQueries({ queryKey: ['library-read-link', user?.id, bookId] })
  }, [refreshingLink, queryClient, user?.id, bookId])

  useEffect(() => {
    if (!book) return
    setPage(initialReaderPage(book.last_page, pageCount || book.last_page || 1))
  }, [book?.id, book?.last_page])

  useEffect(() => {
    const bytes = fileQuery.data
    const canvas = canvasRef.current
    if (!bytes || !canvas || !canRead) return
    let cancelled = false
    setRendering(true)
    setFileError(null)
    void renderPage(bytes, page, canvas)
      .then((count) => {
        if (cancelled) return
        setPageCount(count)
        setPage((current) => Math.min(current, count))
      })
      .catch((error: unknown) => {
        if (cancelled) return
        const message = error instanceof Error ? error.message : ''
        const known = /could not|missing|not available|not configured|not found/i.test(message)
        setFileError(known ? message : 'This PDF file could not be opened.')
      })
      .finally(() => {
        if (!cancelled) setRendering(false)
      })
    return () => {
      cancelled = true
    }
  }, [fileQuery.data, page, canRead])

  const progress = useMutation({
    mutationFn: (nextPage: number) => saveReadingProgress(bookId, nextPage),
    onSuccess: (updated) => {
      const stored = acceptStudentBook(userId, updated)
      queryClient.setQueryData(['library-book', user?.id, bookId], stored)
    },
  })
  const status = useMutation({
    mutationFn: (next: ReadingStatus) => setReadingStatus(bookId, next),
    onSuccess: (updated) => {
      const stored = acceptStudentBook(userId, updated)
      queryClient.setQueryData(['library-book', user?.id, bookId], stored)
    },
  })

  function changePage(nextPage: number) {
    const bounded = Math.min(Math.max(1, nextPage), pageCount || nextPage)
    const write = progressWrite(book?.last_page ?? null, bounded, true)
    setPage(bounded)
    if (write != null && book?.available) progress.mutate(write)
  }

  if (bookQuery.isLoading || refreshingLink || (canRead && !fileQuery.data && (linkQuery.isLoading || fileQuery.isLoading) && !fileError)) {
    return <p className="text-sm text-[var(--color-text-muted)]">Loading PDF…</p>
  }
  if (bookQuery.isError || !book) {
    return <ErrorState message={bookQuery.error instanceof Error ? bookQuery.error.message : 'Could not load this book.'} />
  }
  if (!book.available) {
    return (
      <div className="min-w-0">
        <BackLink />
        <EmptyState title="This resource is no longer available" description="The PDF is hidden. A bookmark or reading status you already saved is kept." />
      </div>
    )
  }
  if (!book.has_file) {
    return (
      <div className="min-w-0">
        <BackLink />
        <EmptyState title="This book has no PDF" description="Open its external resource from the book page." />
      </div>
    )
  }
  const error = fileError ?? (linkQuery.isError || fileQuery.isError ? messageFrom(linkQuery.error ?? fileQuery.error) : null)
  if (error) {
    return (
      <div className="min-w-0">
        <BackLink />
        <ErrorState message={error} />
        <Button type="button" className="mt-3" onClick={() => { setLinkAttempt(0); void queryClient.invalidateQueries({ queryKey: ['library-read-link', user?.id, bookId] }) }}>Retry</Button>
      </div>
    )
  }

  return (
    <div className="min-w-0">
      <BackLink />
      <h1 className="break-words text-2xl font-semibold text-[var(--color-text)]">{book.title}</h1>
      <p className="mt-1 text-sm text-[var(--color-text-muted)]">
        Page {page}{pageCount ? ` of ${pageCount}` : ''}. Opening the PDF does not change your reading status.
      </p>
      {rendering ? <p className="mt-2 text-sm text-[var(--color-text-muted)]">Opening page…</p> : null}
      <div className="mt-4 flex flex-wrap items-center gap-2" role="group" aria-label="PDF pages">
        <Button type="button" aria-label="Previous page" disabled={page <= 1} onClick={() => changePage(page - 1)}>
          <ChevronLeft size={16} /> Previous
        </Button>
        <label className="text-sm text-[var(--color-text-muted)]">
          Page
          <input
            aria-label="Page number"
            className="ml-2 w-16 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-[var(--color-text)]"
            inputMode="numeric"
            value={page}
            onChange={(event) => {
              const next = Number(event.target.value)
              if (Number.isInteger(next)) changePage(next)
            }}
          />
        </label>
        <Button type="button" aria-label="Next page" disabled={pageCount > 0 && page >= pageCount} onClick={() => changePage(page + 1)}>
          Next <ChevronRight size={16} />
        </Button>
      </div>
      <canvas ref={canvasRef} className="mt-4 max-w-full border border-[var(--color-border)] bg-white" />
      <div className="mt-4" role="group" aria-label="Reading status">
        <p className="mb-2 text-sm text-[var(--color-text-muted)]">Choose a status. Nothing is saved until you do.</p>
        <div className="flex flex-wrap gap-2">
          {STATUSES.map((item) => (
            <Button
              key={item.value}
              type="button"
              variant={book.reading_status === item.value ? 'primary' : 'secondary'}
              aria-pressed={book.reading_status === item.value}
              onClick={() => status.mutate(item.value)}
            >
              {item.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}

function BackLink() {
  const { bookId = '' } = useParams()
  return (
    <Link to={`/library/${bookId}`} className="mb-3 inline-flex items-center gap-1 text-sm text-[var(--color-text-muted)]">
      <BookOpen size={14} /> Back to book
    </Link>
  )
}

function messageFrom(error: unknown) {
  return error instanceof Error ? error.message : 'This PDF file could not be opened.'
}

async function renderPage(data: ArrayBuffer, pageNumber: number, canvas: HTMLCanvasElement) {
  const pdfjs = await import('pdfjs-dist/legacy/build/pdf.mjs')
  const worker = await import('pdfjs-dist/legacy/build/pdf.worker.min.mjs?url')
  pdfjs.GlobalWorkerOptions.workerSrc = worker.default
  const source = {
    data: new Uint8Array(data.slice(0)),
    standardFontDataUrl: `${import.meta.env.BASE_URL}standard_fonts/`,
  }
  const doc = await pdfjs.getDocument(source).promise
  const page = await doc.getPage(Math.min(pageNumber, doc.numPages))
  const viewport = page.getViewport({ scale: 1.2 })
  canvas.width = viewport.width
  canvas.height = viewport.height
  await page.render({ canvas, viewport }).promise
  return doc.numPages
}
