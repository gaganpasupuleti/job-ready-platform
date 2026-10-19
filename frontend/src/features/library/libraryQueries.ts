import { queryClient } from '@/queryClient'
import {
  fetchLibraryBook,
  fetchLibraryBooks,
  fetchSavedBooks,
  type StudentBook,
  type StudentBookPage,
} from '@/services/libraryService'
import { redactLibraryPayload, stripBookUrl } from '@/features/library/libraryCache'

function hideBook(userId: string, bookId: string) {
  const apply = <T,>(data: T) => stripBookUrl(data, bookId)
  queryClient.setQueriesData({ queryKey: ['library-book', userId, bookId] }, apply)
  queryClient.setQueriesData({ queryKey: ['library-saved', userId] }, apply)
  queryClient.setQueriesData({ queryKey: ['library-books', userId] }, apply)
  queryClient.removeQueries({ queryKey: ['library-read-link', userId, bookId] })
  queryClient.removeQueries({ queryKey: ['library-file', userId, bookId] })
}

function acceptPayload<T>(userId: string, payload: T, fetchedAt: number): T {
  const next = redactLibraryPayload(userId, payload, fetchedAt)
  const books = Array.isArray(next) ? next : isPage(next) ? next.items : isBook(next) ? [next] : []
  for (const book of books) {
    if (!book.available) hideBook(userId, book.id)
  }
  return next
}

export async function loadLibraryBooks(userId: string, query: string, category: string) {
  const fetchedAt = Date.now()
  return acceptPayload(userId, await fetchLibraryBooks(query, category), fetchedAt)
}

export async function loadSavedBooks(userId: string) {
  const fetchedAt = Date.now()
  return acceptPayload(userId, await fetchSavedBooks(), fetchedAt)
}

export async function loadLibraryBook(userId: string, bookId: string) {
  const fetchedAt = Date.now()
  return acceptPayload(userId, await fetchLibraryBook(bookId), fetchedAt)
}

export function acceptStudentBook(userId: string, book: StudentBook, fetchedAt = Date.now()) {
  return acceptPayload(userId, book, fetchedAt)
}

function isBook(value: unknown): value is StudentBook {
  return Boolean(value && typeof value === 'object' && 'available' in value && 'id' in value)
}

function isPage(value: unknown): value is StudentBookPage {
  return Boolean(value && typeof value === 'object' && 'items' in value && Array.isArray((value as StudentBookPage).items))
}
