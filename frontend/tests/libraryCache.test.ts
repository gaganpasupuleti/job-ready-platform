import assert from 'node:assert/strict'
import { test } from 'node:test'

import { redactBook, redactLibraryPayload, resetLibraryUrlGuard, stripBookUrl } from '../src/features/library/libraryCache.ts'

const bookId = '74bb4a52-2920-4e5e-9754-6e5724eace66'
const userId = 'student-1'
const url = 'https://example.com/jobready-local-library-fixture'

const published = {
  id: bookId,
  title: 'Local library fixture accept',
  available: true,
  external_url: url,
}

test('an unavailable book drops its URL and a stale earlier response cannot restore it', () => {
  resetLibraryUrlGuard()
  const archived = redactBook(userId, { ...published, available: false, external_url: null }, 200)
  assert.equal(archived.external_url, null)
  assert.equal(archived.available, false)

  const stale = redactBook(userId, published, 100)
  assert.equal(stale.available, false)
  assert.equal(stale.external_url, null)

  const other = redactBook('student-2', published, 100)
  assert.equal(other.external_url, url)

  const republished = redactBook(userId, published, 300)
  assert.equal(republished.available, true)
  assert.equal(republished.external_url, url)
})

test('saved lists and search caches lose the URL for that book only', () => {
  resetLibraryUrlGuard()
  const saved = stripBookUrl(
    [
      published,
      { id: 'other', available: true, external_url: 'https://example.com/other' },
    ],
    bookId,
  )
  assert.equal(saved[0].external_url, null)
  assert.equal(saved[0].available, false)
  assert.equal(saved[1].external_url, 'https://example.com/other')

  const page = stripBookUrl({ items: [published], categories: ['Local fixtures'] }, bookId)
  assert.equal(page.items[0].external_url, null)
  assert.deepEqual(page.categories, ['Local fixtures'])

  const fetchedAt = 50
  const redacted = redactLibraryPayload(userId, { items: [{ ...published, available: false, external_url: null }], categories: [] }, fetchedAt)
  assert.equal(redacted.items[0].external_url, null)
  const stalePage = redactLibraryPayload(userId, { items: [published], categories: [] }, fetchedAt - 1)
  assert.equal(stalePage.items[0].external_url, null)
})
