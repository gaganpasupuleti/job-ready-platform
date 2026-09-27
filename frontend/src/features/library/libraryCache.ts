/** Keeps an archived resource URL from returning through another cached query. */

export type CacheBook = {
  id: string
  available: boolean
  external_url: string | null
}

export type CacheBookPage = {
  items: CacheBook[]
  categories: string[]
}

const hiddenSince = new Map<string, number>()

function guardKey(userId: string, bookId: string) {
  return `${userId}:${bookId}`
}

export function resetLibraryUrlGuard() {
  hiddenSince.clear()
}

export function redactBook<T extends CacheBook>(userId: string, book: T, fetchedAt: number): T {
  if (!book.available) {
    const key = guardKey(userId, book.id)
    const current = hiddenSince.get(key)
    if (current == null || fetchedAt >= current) hiddenSince.set(key, fetchedAt)
    return book.external_url == null ? book : { ...book, external_url: null }
  }
  const hidden = hiddenSince.get(guardKey(userId, book.id))
  if (hidden != null && fetchedAt < hidden) {
    return { ...book, available: false, external_url: null }
  }
  if (hidden != null) hiddenSince.delete(guardKey(userId, book.id))
  return book
}

export function redactLibraryPayload<T>(userId: string, payload: T, fetchedAt: number): T {
  if (Array.isArray(payload)) {
    return payload.map((item) => (isBook(item) ? redactBook(userId, item, fetchedAt) : item)) as T
  }
  if (isPage(payload)) {
    return { ...payload, items: payload.items.map((item) => redactBook(userId, item, fetchedAt)) }
  }
  if (isBook(payload)) return redactBook(userId, payload, fetchedAt) as T
  return payload
}

export function stripBookUrl<T>(data: T, bookId: string): T {
  if (Array.isArray(data)) {
    return data.map((item) => (isBook(item) && item.id === bookId ? hide(item) : item)) as T
  }
  if (isPage(data)) {
    return { ...data, items: data.items.map((item) => (item.id === bookId ? hide(item) : item)) }
  }
  if (isBook(data) && data.id === bookId) return hide(data) as T
  return data
}

function hide<T extends CacheBook>(book: T): T {
  return book.available === false && book.external_url == null ? book : { ...book, available: false, external_url: null }
}

function isBook(value: unknown): value is CacheBook {
  if (!value || typeof value !== 'object') return false
  const book = value as CacheBook
  return typeof book.id === 'string' && typeof book.available === 'boolean' && 'external_url' in book
}

function isPage(value: unknown): value is CacheBookPage {
  if (!value || typeof value !== 'object' || !('items' in value)) return false
  return Array.isArray((value as CacheBookPage).items)
}
