import assert from 'node:assert/strict'
import test from 'node:test'

import { sourceChoice, uploadPhase, validatePdfFile } from '../src/features/library/uploadModel.ts'

const MAX = 20 * 1024 * 1024

test('upload validation and exclusive source state', () => {
  assert.equal(validatePdfFile('notes.txt', 'application/pdf', 12, MAX), 'Choose a .pdf file.')
  assert.equal(validatePdfFile('notes.pdf', 'text/plain', 12, MAX), 'Only PDF files can be uploaded.')
  assert.equal(validatePdfFile('notes.pdf', 'application/pdf', 0, MAX), 'The PDF file is empty.')
  assert.equal(validatePdfFile('notes.pdf', 'application/pdf', MAX + 1, MAX), 'The PDF is too large.')
  assert.equal(validatePdfFile('notes.pdf', 'application/pdf', 12, MAX), null)
  const both = sourceChoice('https://example.com/book', 'notes.pdf', false)
  assert.equal(both.exclusiveError, 'Choose either an https link or a PDF.')
  const attached = sourceChoice('', null, true)
  assert.equal(attached.hasFile, true)
  assert.equal(attached.needsSource, false)
  const empty = sourceChoice('', null, false)
  assert.equal(empty.needsSource, true)
})

test('upload phase shows loading and failure without dropping the saved file', () => {
  assert.equal(uploadPhase('idle', 'start'), 'uploading')
  assert.equal(uploadPhase('uploading', 'fail'), 'failed')
  assert.equal(uploadPhase('failed', 'success'), 'idle')
  assert.equal(sourceChoice('', null, true).hasFile, true)
})
