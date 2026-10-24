import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, BookOpen, ExternalLink } from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { formatLibraryTitle, isImportAuthor, readingStatusLabel, readingStatusVariant } from '@/features/library/libraryPresentation'
import { EmptyState, ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { sectionStaleMessage, sectionUnavailable } from '@/features/dashboard/overviewModel'
import { useAuth } from '@/hooks/useAuth'
import { acceptStudentBook, loadLibraryBook } from '@/features/library/libraryQueries'
import {
  bookmarkBook,
  setReadingStatus,
  unbookmarkBook,
  type ReadingStatus,
  type StudentBook,
} from '@/services/libraryService'

const STATUSES: { value: ReadingStatus; label: string }[] = [
  { value: 'not_started', label: 'Not started' },
  { value: 'reading', label: 'Reading' },
  { value: 'completed', label: 'Completed' },
]

function online() {
  return typeof navigator === 'undefined' ? true : navigator.onLine
}

export function LibraryBookPage() {
  const { bookId = '' } = useParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [actionError, setActionError] = useState('')
  const book = useQuery({
    queryKey: ['library-book', user?.id, bookId],
    queryFn: () => loadLibraryBook(user?.id ?? '', bookId),
    enabled: Boolean(user?.id && bookId),
  })
  const missing = sectionUnavailable(book)
  const stale = sectionStaleMessage(book, online())

  async function refresh(next: StudentBook) {
    const stored = user?.id ? acceptStudentBook(user.id, next) : next
    queryClient.setQueryData(['library-book', user?.id, bookId], stored)
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['library-books', user?.id] }),
      queryClient.invalidateQueries({ queryKey: ['library-saved', user?.id] }),
    ])
  }

  async function toggleBookmark() {
    if (!book.data) return
    setActionError('')
    try {
      const next = book.data.bookmarked ? await unbookmarkBook(book.data.id) : await bookmarkBook(book.data.id)
      await refresh(next)
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Could not update the bookmark.')
    }
  }

  async function chooseStatus(status: ReadingStatus) {
    if (!book.data?.available) return
    setActionError('')
    try {
      await refresh(await setReadingStatus(book.data.id, status))
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Could not save the reading status.')
    }
  }

  return (
    <div className="mx-auto min-w-0 max-w-3xl space-y-4">
      <Link
        to="/library"
        className="inline-flex items-center gap-1 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-accent)]"
      >
        <ArrowLeft size={14} aria-hidden /> Back to library
      </Link>
      {book.isPending && book.isFetching && book.data == null ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading resource</p>
      ) : null}
      {missing ? (
        <div className="space-y-3">
          <ErrorState message={book.error instanceof Error ? book.error.message : 'This resource could not be loaded.'} />
          <Button type="button" variant="secondary" size="sm" onClick={() => void book.refetch()}>
            Retry
          </Button>
        </div>
      ) : null}
      {stale ? (
        <div className="space-y-3">
          <ErrorState message={stale} />
          <Button type="button" variant="secondary" size="sm" onClick={() => void book.refetch()}>
            Retry
          </Button>
        </div>
      ) : null}
      {book.data ? <BookDetail book={book.data} actionError={actionError} onBookmark={() => void toggleBookmark()} onStatus={(status) => void chooseStatus(status)} /> : null}
    </div>
  )
}

function BookDetail({
  book,
  actionError,
  onBookmark,
  onStatus,
}: {
  book: StudentBook
  actionError: string
  onBookmark: () => void
  onStatus: (status: ReadingStatus) => void
}) {
  const title = formatLibraryTitle(book.title)
  const subtitle = isImportAuthor(book.author) ? book.category : `${book.author} · ${book.category}`

  return (
    <Card className="min-w-0 overflow-hidden">
      <div className="flex flex-col gap-4 border-b border-[var(--color-border)] bg-[var(--color-surface-muted)] p-5 sm:flex-row sm:items-start">
        <div
          className="flex h-20 w-16 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-accent)]"
          aria-hidden
        >
          <BookOpen size={28} strokeWidth={1.5} />
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-lg font-semibold leading-snug text-[var(--color-text)]">{title}</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">{subtitle}</p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            <Badge>{book.category}</Badge>
            {isImportAuthor(book.author) ? <Badge variant="accent">Imported</Badge> : null}
            {book.available ? (
              <Badge variant={readingStatusVariant(book.reading_status)}>{readingStatusLabel(book.reading_status)}</Badge>
            ) : (
              <Badge variant="warning">Unavailable</Badge>
            )}
          </div>
        </div>
      </div>
      <div className="p-5">
      {book.description ? <p className="mb-4 break-words text-sm text-[var(--color-text)]">{book.description}</p> : null}
      <div className="mb-5 flex flex-wrap gap-2">
        {book.available && book.has_file ? (
          <Link to={`/library/${book.id}/read`} className="jr-action-link">
            {book.last_page ? `Resume at page ${book.last_page}` : 'Read PDF'}
          </Link>
        ) : null}
        {book.available && book.external_url ? (
          <a
            href={book.external_url}
            target="_blank"
            rel="noopener noreferrer"
            className="jr-action-link jr-action-link--secondary inline-flex gap-1"
          >
            <ExternalLink size={14} aria-hidden /> External link
          </a>
        ) : null}
        <Button type="button" variant="secondary" size="sm" onClick={onBookmark}>
          {book.bookmarked ? 'Remove bookmark' : 'Bookmark'}
        </Button>
      </div>
      {book.available && book.has_file ? (
        <p className="mb-4 text-xs text-[var(--color-text-muted)]">
          Reading in the built-in viewer does not change your status until you choose one below.
        </p>
      ) : null}
      {book.available && book.external_url ? (
        <p className="mb-4 text-xs text-[var(--color-text-muted)]">
          External links leave JobReady and do not update reading status.
        </p>
      ) : null}
      {book.available && !book.external_url && !book.has_file ? (
        <p className="mb-4 text-sm text-[var(--color-text-muted)]">No PDF or link is attached.</p>
      ) : null}
      {!book.available ? (
        <div className="mb-4">
          <EmptyState
            title="This resource is no longer available"
            description="The link is hidden. A bookmark or reading status you already saved is kept."
          />
        </div>
      ) : null}
      <div className="mt-2 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-4" role="group" aria-label="Reading status">
        <p className="text-sm font-medium text-[var(--color-text)]">Reading status</p>
        <p className="mb-3 text-xs text-[var(--color-text-muted)]">Choose a status. Nothing is saved until you tap one.</p>
        <div className="flex flex-wrap gap-2">
          {STATUSES.map((item) => (
            <Button
              key={item.value}
              type="button"
              size="sm"
              variant={book.reading_status === item.value ? 'primary' : 'secondary'}
              disabled={!book.available}
              aria-pressed={book.reading_status === item.value}
              onClick={() => onStatus(item.value)}
            >
              {item.label}
            </Button>
          ))}
        </div>
      </div>
      {actionError ? <p className="mt-3 text-sm text-[var(--color-text)]">{actionError}</p> : null}
      </div>
    </Card>
  )
}
