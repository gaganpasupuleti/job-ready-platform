import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BookMarked } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { FilterDisclosure } from '@/components/layout/FilterDisclosure'
import { PageIntro } from '@/components/layout/PageIntro'
import { EmptyState, ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { LibraryBookCard } from '@/features/library/LibraryBookCard'
import { dedupeLibraryBooks } from '@/features/library/libraryPresentation'
import { sectionStaleMessage, sectionUnavailable } from '@/features/dashboard/overviewModel'
import { useAuth } from '@/hooks/useAuth'
import { loadLibraryBooks, loadSavedBooks } from '@/features/library/libraryQueries'

function online() {
  return typeof navigator === 'undefined' ? true : navigator.onLine
}

export function LibraryPage() {
  const { user } = useAuth()
  const [query, setQuery] = useState('')
  const [submitted, setSubmitted] = useState('')
  const [category, setCategory] = useState('')
  const [filtersOpen, setFiltersOpen] = useState(false)
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

  const published = useMemo(() => dedupeLibraryBooks(books.data?.items ?? []), [books.data?.items])
  const rawCount = books.data?.items.length ?? 0
  const hiddenDupes = rawCount - published.length
  const catalogTotal = books.data?.total_published ?? books.data?.total ?? rawCount
  const filteredTotal = books.data?.total ?? rawCount
  const hasFilters = Boolean(submitted || category)
  const activeFilterCount = (submitted ? 1 : 0) + (category ? 1 : 0)

  useEffect(() => {
    if (activeFilterCount > 0) setFiltersOpen(true)
  }, [activeFilterCount])

  const catalogAside =
    books.data ? (
      <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-center sm:min-w-[10rem] sm:text-right">
        <p className="text-xl font-semibold tabular-nums leading-none text-[var(--color-text)]">{catalogTotal}</p>
        <p className="mt-1 text-[11px] font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
          Published books
        </p>
        {hiddenDupes > 0 ? (
          <p className="mt-1.5 text-xs text-[var(--color-text-muted)]">
            {published.length} unique titles · {hiddenDupes} duplicates hidden in list
          </p>
        ) : null}
        {hasFilters && filteredTotal !== catalogTotal ? (
          <p className="mt-1 text-xs text-[var(--color-accent)]">{filteredTotal} match your filters</p>
        ) : null}
      </div>
    ) : null

  return (
    <div className="min-w-0 space-y-6">
      <PageIntro
        title="Library"
        description="Browse published books and PDFs. Open a title to read in-app or save your reading status."
        aside={catalogAside}
      />

      {saved.data && saved.data.length > 0 ? (
        <Card className="min-w-0">
          <CardHeader
            title="Your shelf"
            description="Bookmarks and reading progress stay here if a resource is archived."
          />
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
          <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {saved.data.map((book) => (
              <li key={book.id}>
                <LibraryBookCard book={book} />
              </li>
            ))}
          </ul>
        </Card>
      ) : saved.isPending && saved.isFetching ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading your shelf…</p>
      ) : (
        <Card className="min-w-0 border-dashed">
          <div className="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
            <BookMarked size={18} aria-hidden />
            Bookmark a book or set a reading status to see it on your shelf.
          </div>
        </Card>
      )}

      <Card className="min-w-0">
        <CardHeader title="Published resources" description="Search by title or author, or filter by category." />
        <FilterDisclosure
          title="Search catalog"
          open={filtersOpen}
          onOpenChange={setFiltersOpen}
          activeCount={activeFilterCount}
          className="mb-5"
        >
        <form
          className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(10rem,14rem)_auto] sm:items-end"
          onSubmit={(event) => {
            event.preventDefault()
            setSubmitted(query.trim())
          }}
        >
          <label className="min-w-0 text-sm">
            <span className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]">Search</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Title or author"
              className="w-full min-w-0 rounded-[var(--radius-control)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-subtle)]"
            />
          </label>
          <label className="min-w-0 text-sm">
            <span className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]">Category</span>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="w-full min-w-0 rounded-[var(--radius-control)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]"
            >
              <option value="">All categories</option>
              {(books.data?.categories ?? []).map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <div className="flex gap-2 sm:justify-end">
            <Button type="submit" variant="primary" size="sm">
              Search
            </Button>
            {submitted || category ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => {
                  setQuery('')
                  setSubmitted('')
                  setCategory('')
                }}
              >
                Clear
              </Button>
            ) : null}
          </div>
        </form>
        </FilterDisclosure>
        {books.isPending && books.isFetching && books.data == null ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading published resources…</p>
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
        {books.data && published.length === 0 ? (
          <EmptyState title="No published resources" description="Draft and archived resources stay hidden." />
        ) : null}
        {published.length > 0 ? (
          <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {published.map((book) => (
              <li key={book.id}>
                <LibraryBookCard book={book} />
              </li>
            ))}
          </ul>
        ) : null}
      </Card>
    </div>
  )
}
