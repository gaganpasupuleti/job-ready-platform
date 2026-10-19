import type { StudentBook } from '@/services/libraryService'

/** Turn ingest filenames / ALL CAPS titles into readable headings. */
export function formatLibraryTitle(raw: string): string {
  const trimmed = raw.trim()
  if (!trimmed) return trimmed
  const letters = trimmed.replace(/[^a-zA-Z]/g, '')
  const upperCount = trimmed.replace(/[^A-Z]/g, '').length
  if (letters.length >= 10 && upperCount / letters.length > 0.8) {
    return trimmed
      .toLowerCase()
      .split(/\s+/)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }
  return trimmed
}

export function isImportAuthor(author: string) {
  return /cloudflare\s*import/i.test(author.trim())
}

export function readingStatusLabel(status: StudentBook['reading_status']) {
  if (status === 'reading') return 'Reading'
  if (status === 'completed') return 'Completed'
  if (status === 'not_started') return 'Not started'
  return 'No status'
}

export function readingStatusVariant(status: StudentBook['reading_status']): 'default' | 'accent' | 'success' {
  if (status === 'reading') return 'accent'
  if (status === 'completed') return 'success'
  return 'default'
}

/** Bulk ingest can register the same title under different folders. */
export function dedupeLibraryBooks(items: StudentBook[]): StudentBook[] {
  const seen = new Set<string>()
  const out: StudentBook[] = []
  for (const book of items) {
    const key = book.title.trim().toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    out.push(book)
  }
  return out
}
