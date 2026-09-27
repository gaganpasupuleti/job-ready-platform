import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { EmptyState, ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { sectionStaleMessage, sectionUnavailable } from '@/features/dashboard/overviewModel'
import { useAuth } from '@/hooks/useAuth'
import { loadLibraryBooks, loadSavedBooks } from '@/features/library/libraryQueries'
import { type StudentBook } from '@/services/libraryService'

function online() {
  return typeof navigator === 'undefined' ? true : navigator.onLine
}

function statusText(status: StudentBook['reading_status']) {
  if (status === 'reading') return 'Reading'
  if (status === 'completed') return 'Completed'
  if (status === 'not_started') return 'Not started'
  return 'No reading status saved'
}

export function LibraryPage() {
  const { user } = useAuth()
  const [query, setQuery] = useState('')
  const [submitted, setSubmitted] = useState('')
  const [category, setCategory] = useState('')
  const books = useQuery({
    queryKey: ['library-books', user?.id, submitted, category],
    queryFn: () => loadLibraryBooks(user?.id ?? '', submitted, category),
    enabled: Boolean(user?.id),
  })
  const saved = useQuery({
    queryKey: ['library-saved', user?.id],
    queryFn: () => loadSavedBooks(user?.id ?? ''),
    enabled: Boolean(user?.id),
  })
  const booksMissing = sectionUnavailable(books)
  const savedMissing = sectionUnavailable(saved)
  const booksStale = sectionStaleMessage(books, online())
  const savedStale = sectionStaleMessage(saved, online())

  return (
    <div className="min-w-0 space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-[var(--color-text)]">Library</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Published external resources. Opening a link does not record reading.
        </p>
      </div>

      <Card className="min-w-0">
        <CardHeader title="Your saved records" description="Bookmarks and reading status stay here if a resource is archived." />
        {saved.isPending && saved.isFetching && saved.data == null ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading saved records</p>
        ) : null}
        {savedMissing ? (
          <div className="space-y-3">
            <ErrorState message="Saved records could not be loaded." />
            <Button type="button" variant="secondary" size="sm" onClick={() => void saved.refetch()}>
              Retry
            </Button>
          </div>
        ) : null}
        {savedStale ? (
          <div className="mb-3 space-y-3">
            <ErrorState message={savedStale} />
            <Button type="button" variant="secondary" size="sm" onClick={() => void saved.refetch()}>
              Retry
            </Button>
          </div>
        ) : null}
        {saved.data && saved.data.length === 0 ? <EmptyState title="No saved library records" /> : null}
        {saved.data && saved.data.length > 0 ? (
          <ul className="space-y-2">
            {saved.data.map((book) => (
              <BookRow key={book.id} book={book} />
            ))}
          </ul>
        ) : null}
      </Card>

      <Card className="min-w-0">
        <CardHeader title="Published resources" />
        <form
          className="mb-4 grid gap-2 sm:grid-cols-[1fr_auto_auto]"
          onSubmit={(event) => {
            event.preventDefault()
            setSubmitted(query.trim())
          }}
        >
          <label className="min-w-0 text-sm">
            <span className="mb-1 block text-xs text-[var(--color-text-muted)]">Search title or author</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="w-full min-w-0 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            />
          </label>
          <label className="min-w-0 text-sm">
            <span className="mb-1 block text-xs text-[var(--color-text-muted)]">Category</span>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="w-full min-w-0 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            >
              <option value="">All categories</option>
              {(books.data?.categories ?? []).map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <div className="self-end">
            <Button type="submit" variant="secondary" size="sm">
              Search
            </Button>
          </div>
        </form>
        {books.isPending && books.isFetching && books.data == null ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading published resources</p>
        ) : null}
        {booksMissing ? (
          <div className="space-y-3">
            <ErrorState message="Published resources could not be loaded." />
            <Button type="button" variant="secondary" size="sm" onClick={() => void books.refetch()}>
              Retry
            </Button>
          </div>
        ) : null}
        {booksStale ? (
          <div className="mb-3 space-y-3">
            <ErrorState message={booksStale} />
            <Button type="button" variant="secondary" size="sm" onClick={() => void books.refetch()}>
              Retry
            </Button>
          </div>
        ) : null}
        {books.data && books.data.items.length === 0 ? (
          <EmptyState title="No published resources" description="Draft and archived resources stay hidden." />
        ) : null}
        {books.data && books.data.items.length > 0 ? (
          <ul className="space-y-2">
            {books.data.items.map((book) => (
              <BookRow key={book.id} book={book} />
            ))}
          </ul>
        ) : null}
      </Card>
    </div>
  )
}

function BookRow({ book }: { book: StudentBook }) {
  return (
    <li className="min-w-0">
      <Link
        to={`/library/${book.id}`}
        className="block rounded-md border border-[var(--color-border)] p-3 hover:border-[var(--color-accent)]"
      >
        <p className="break-words text-sm font-medium text-[var(--color-text)]">{book.title}</p>
        <p className="break-words text-xs text-[var(--color-text-muted)]">
          {book.author} · {book.category} · {book.available ? statusText(book.reading_status) : 'Unavailable'}
          {book.bookmarked ? ' · Bookmarked' : ''}
        </p>
      </Link>
    </li>
  )
}
