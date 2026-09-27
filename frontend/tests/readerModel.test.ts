import assert from 'node:assert/strict'
import test from 'node:test'

import { initialReaderPage, progressWrite, readerFileUrl } from '../src/features/library/readerModel.ts'

test('the reader resumes a saved page and does not write merely by opening', () => {
  assert.equal(initialReaderPage(null, 2), 1)
  assert.equal(initialReaderPage(2, 2), 2)
  assert.equal(initialReaderPage(9, 2), 2)
  assert.equal(progressWrite(null, 1, false), null)
  assert.equal(progressWrite(2, 2, true), null)
  assert.equal(progressWrite(1, 2, true), 2)
})

test('an unavailable book cannot keep a cached file URL', () => {
  assert.equal(readerFileUrl(false, true, 'https://example.com/signed-file'), null)
  assert.equal(readerFileUrl(true, false, 'https://example.com/signed-file'), null)
  assert.equal(readerFileUrl(true, true, '/api/v1/library/books/1/file'), '/api/v1/library/books/1/file')
})
