import { BookOpen, ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Badge } from '@/components/common/Badge'
import { cn } from '@/utils/cn'
import {
  formatLibraryTitle,
  isImportAuthor,
  readingStatusLabel,
  readingStatusVariant,
} from '@/features/library/libraryPresentation'
import type { StudentBook } from '@/services/libraryService'

type LibraryBookCardProps = {
  book: StudentBook
  className?: string
}

export function LibraryBookCard({ book, className }: LibraryBookCardProps) {
  const title = formatLibraryTitle(book.title)
  const showAuthor = book.author.trim() && !isImportAuthor(book.author)

  return (
    <Link
      to={`/library/${book.id}`}
      className={cn(
        'group flex min-h-[5.5rem] gap-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-3 transition-colors hover:border-[var(--color-accent)] hover:bg-[var(--color-surface-muted)]',
        !book.available && 'opacity-70',
        className,
      )}
    >
      <div
        className="flex h-[4.25rem] w-12 shrink-0 flex-col items-center justify-center rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-accent-muted)] text-[var(--color-accent)]"
        aria-hidden
      >
        <BookOpen size={20} strokeWidth={1.75} />
        {book.has_file ? (
          <span className="mt-0.5 text-[9px] font-semibold uppercase tracking-wide">PDF</span>
        ) : null}
      </div>
      <div className="min-w-0 flex-1">
        <p className="line-clamp-2 text-sm font-semibold leading-snug text-[var(--color-text)]">{title}</p>
        {showAuthor ? (
          <p className="mt-1 line-clamp-1 text-xs text-[var(--color-text-muted)]">{book.author}</p>
        ) : null}
        <div className="mt-2 flex flex-wrap gap-1.5">
          <Badge>{book.category}</Badge>
          {isImportAuthor(book.author) ? <Badge variant="accent">Imported</Badge> : null}
          <Badge variant={book.available ? readingStatusVariant(book.reading_status) : 'warning'}>
            {book.available ? readingStatusLabel(book.reading_status) : 'Unavailable'}
          </Badge>
          {book.bookmarked ? <Badge variant="accent">Saved</Badge> : null}
        </div>
      </div>
      <span
        className="hidden shrink-0 self-center text-xs font-medium text-[var(--color-accent)] sm:inline-flex sm:items-center sm:gap-0.5 sm:opacity-0 sm:transition-opacity group-hover:sm:opacity-100"
      >
        Open <ChevronRight size={14} aria-hidden />
      </span>
    </Link>
  )
}
