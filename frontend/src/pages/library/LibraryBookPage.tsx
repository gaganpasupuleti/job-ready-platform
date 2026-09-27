import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
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
    <div className="min-w-0 space-y-4">
      <Link to="/library" className="text-sm text-[var(--color-accent)] hover:underline">
        Library
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
  return (
    <Card className="min-w-0">
      <CardHeader title={book.title} description={`${book.author} · ${book.category}`} />
      {book.description ? <p className="mb-4 break-words text-sm text-[var(--color-text)]">{book.description}</p> : null}
      {book.available && book.external_url ? (
        <p className="mb-4">
          <a
            href={book.external_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-[var(--color-accent)] hover:underline"
          >
            Open external resource
          </a>
          <span className="mt-1 block break-words text-xs text-[var(--color-text-muted)]">
            This https link leaves JobReady. Opening it does not set a reading status.
          </span>
        </p>
      ) : null}
      {book.available && book.has_file ? (
        <p className="mb-4">
          <Link to={`/library/${book.id}/read`} className="text-sm text-[var(--color-accent)] hover:underline">
            Read PDF
          </Link>
          <span className="mt-1 block break-words text-xs text-[var(--color-text-muted)]">
            {book.last_page ? `Resume at page ${book.last_page}. ` : ''}Opening the PDF does not change your reading status.
          </span>
        </p>
      ) : null}
      {!book.available ? (
        <div className="mb-4">
          <EmptyState
            title="This resource is no longer available"
            description="The link is hidden. A bookmark or reading status you already saved is kept."
          />
        </div>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="secondary" size="sm" onClick={onBookmark}>
          {book.bookmarked ? 'Remove bookmark' : 'Bookmark'}
        </Button>
      </div>
      <div className="mt-4" role="group" aria-label="Reading status">
        <p className="text-xs text-[var(--color-text-muted)]">Reading status</p>
        <p className="mb-2 text-xs text-[var(--color-text-muted)]">Choose a status. Nothing is saved until you do.</p>
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
    </Card>
  )
}
