import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, ChevronLeft, ChevronRight, Maximize2, Minimize2 } from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { EmptyState, ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { formatLibraryTitle, readingStatusLabel, readingStatusVariant } from '@/features/library/libraryPresentation'
import { useElementFullscreen } from '@/features/library/useElementFullscreen'
import { cn } from '@/utils/cn'
import { acceptStudentBook, loadLibraryBook } from '@/features/library/libraryQueries'
import { initialReaderPage, progressWrite } from '@/features/library/readerModel'
import { useAuth } from '@/hooks/useAuth'
import { openLibraryPdf } from '@/lib/renderLibraryPdf'
import { fetchLibraryBookFile, saveReadingProgress, setReadingStatus, type ReadingStatus, type StudentBook } from '@/services/libraryService'

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
  const readerStage = useElementFullscreen<HTMLDivElement>()
  const pageScale = readerStage.active ? 1.7 : 1.2
  const [page, setPage] = useState(1)
  const [pageCount, setPageCount] = useState(0)
  const [fileError, setFileError] = useState<string | null>(null)
  const [rendering, setRendering] = useState(false)
  const userId = user?.id ?? ''

  const bookQuery = useQuery({
    queryKey: ['library-book', user?.id, bookId],
    queryFn: () => loadLibraryBook(userId, bookId),
    enabled: Boolean(user?.id && bookId),
    retry: false,
  })
  const book = bookQuery.data
  const canRead = Boolean(book?.available && book.has_file)
  const fileQuery = useQuery({
    queryKey: ['library-file', user?.id, bookId],
    queryFn: async () => {
      const current = queryClient.getQueryData<StudentBook>(['library-book', user?.id, bookId])
      if (!current?.available) throw new Error('This resource is not available.')
      const bytes = await fetchLibraryBookFile(bookId)
      const after = queryClient.getQueryData<StudentBook>(['library-book', user?.id, bookId])
      if (!after?.available) throw new Error('This resource is not available.')
      return bytes
    },
    enabled: Boolean(canRead && bookId),
    retry: false,
    structuralSharing: false,
  })

  useEffect(() => {
    if (!book) return
    setPage(initialReaderPage(book.last_page, pageCount || book.last_page || 1))
  }, [book?.id, book?.last_page])

  useEffect(() => {
    const bytes = fileQuery.data
    if (!bytes || !canRead) return
    let cancelled = false
    setRendering(true)
    setFileError(null)

    const buffer = bytes

    async function paint() {
      let canvas = canvasRef.current
      if (!canvas) {
        await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
        canvas = canvasRef.current
      }
      if (cancelled || !canvas) return
      try {
        const doc = await openLibraryPdf(buffer)
        if (cancelled) return
        setPageCount(doc.numPages)
        setPage((current) => Math.min(current, doc.numPages))
        await doc.renderPage(page, canvas, pageScale)
      } catch (error: unknown) {
        if (cancelled) return
        const message = error instanceof Error ? error.message : ''
        const known = /could not|missing|not available|not configured|not found/i.test(message)
        setFileError(known ? message : 'This PDF file could not be opened.')
      } finally {
        if (!cancelled) setRendering(false)
      }
    }

    void paint()
    return () => {
      cancelled = true
    }
  }, [fileQuery.data, page, canRead, pageScale])

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

  if (bookQuery.isLoading || (canRead && !fileQuery.data && fileQuery.isLoading && !fileError)) {
    return (
      <div className="mx-auto max-w-4xl py-12 text-center text-sm text-[var(--color-text-muted)]">Loading PDF…</div>
    )
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
  const error = fileError ?? (fileQuery.isError ? messageFrom(fileQuery.error) : null)
  if (error) {
    return (
      <div className="min-w-0">
        <BackLink />
        <ErrorState message={error} />
        <Button type="button" className="mt-3" onClick={() => void queryClient.invalidateQueries({ queryKey: ['library-file', user?.id, bookId] })}>Retry</Button>
      </div>
    )
  }

  const title = formatLibraryTitle(book.title)

  return (
    <div className="mx-auto min-w-0 max-w-4xl space-y-4 pb-10">
      <BackLink />
      <header className="space-y-2">
        <h1 className="text-lg font-semibold leading-snug text-[var(--color-text)] sm:text-xl">{title}</h1>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={readingStatusVariant(book.reading_status)}>{readingStatusLabel(book.reading_status)}</Badge>
          <span className="text-sm text-[var(--color-text-muted)]">
            Page {page}{pageCount ? ` of ${pageCount}` : ''}
          </span>
          {rendering ? <span className="text-xs text-[var(--color-text-muted)]">Rendering…</span> : null}
        </div>
      </header>

      <div
        ref={readerStage.ref}
        className={cn(
          'overflow-hidden rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[#525659]',
          readerStage.active && 'flex h-full flex-col border-0 rounded-none',
        )}
      >
        <div
          className={cn(
            'flex flex-wrap items-center justify-between gap-3 border-b border-black/20 bg-[var(--color-surface)] p-3',
            !readerStage.active && 'sticky top-0 z-10 shadow-sm',
          )}
          role="group"
          aria-label="PDF pages"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Button type="button" size="sm" aria-label="Previous page" disabled={page <= 1} onClick={() => changePage(page - 1)}>
              <ChevronLeft size={16} /> Prev
            </Button>
            <label className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
              Page
              <input
                aria-label="Page number"
                className="w-14 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-center text-sm text-[var(--color-text)]"
                inputMode="numeric"
                value={page}
                onChange={(event) => {
                  const next = Number(event.target.value)
                  if (Number.isInteger(next)) changePage(next)
                }}
              />
              {pageCount ? <span>of {pageCount}</span> : null}
            </label>
            <Button
              type="button"
              size="sm"
              aria-label="Next page"
              disabled={pageCount > 0 && page >= pageCount}
              onClick={() => changePage(page + 1)}
            >
              Next <ChevronRight size={16} />
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {!readerStage.active ? (
              <p className="hidden text-xs text-[var(--color-text-subtle)] sm:block">Page changes save automatically.</p>
            ) : (
              <p className="max-w-[12rem] truncate text-xs text-[var(--color-text-muted)]">{title}</p>
            )}
            <Button
              type="button"
              size="sm"
              variant="secondary"
              aria-label={readerStage.active ? 'Exit full screen' : 'Enter full screen'}
              aria-pressed={readerStage.active}
              onClick={readerStage.toggle}
            >
              {readerStage.active ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              <span className="hidden sm:inline">{readerStage.active ? 'Exit' : 'Full screen'}</span>
            </Button>
          </div>
        </div>
        <div className={cn('flex min-h-[50vh] flex-1 justify-center overflow-auto p-4 sm:p-6', readerStage.active && 'min-h-0')}>
          <canvas
            ref={canvasRef}
            className={cn(
              'max-w-full bg-white shadow-lg',
              readerStage.active ? 'max-h-[calc(100vh-4.5rem)]' : 'max-h-[min(78vh,900px)]',
            )}
          />
        </div>
      </div>

      {!readerStage.active ? (
        <div role="group" aria-label="Reading status">
          <Card className="p-4">
            <p className="text-sm font-medium text-[var(--color-text)]">Reading status</p>
            <p className="mb-3 text-xs text-[var(--color-text-muted)]">Optional — pick when you start or finish the book.</p>
            <div className="flex flex-wrap gap-2">
              {STATUSES.map((item) => (
                <Button
                  key={item.value}
                  type="button"
                  size="sm"
                  variant={book.reading_status === item.value ? 'primary' : 'secondary'}
                  aria-pressed={book.reading_status === item.value}
                  onClick={() => status.mutate(item.value)}
                >
                  {item.label}
                </Button>
              ))}
            </div>
          </Card>
        </div>
      ) : null}
    </div>
  )
}

function BackLink() {
  const { bookId = '' } = useParams()
  return (
    <Link
      to={`/library/${bookId}`}
      className="inline-flex items-center gap-1 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-accent)]"
    >
      <ArrowLeft size={14} aria-hidden /> Back to book details
    </Link>
  )
}

function messageFrom(error: unknown) {
  return error instanceof Error ? error.message : 'This PDF file could not be opened.'
}
