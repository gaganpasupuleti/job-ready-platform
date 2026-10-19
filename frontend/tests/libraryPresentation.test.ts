import { describe, expect, it } from 'vitest'

import { dedupeLibraryBooks, formatLibraryTitle } from '@/features/library/libraryPresentation'
import type { StudentBook } from '@/services/libraryService'

function book(id: string, title: string): StudentBook {
  return {
    id,
    title,
    author: 'Cloudflare import',
    description: '',
    category: 'Imported',
    available: true,
    has_file: true,
    external_url: null,
    bookmarked: false,
    reading_status: null,
    last_page: null,
  }
}

describe('formatLibraryTitle', () => {
  it('title-cases screaming ingest filenames', () => {
    expect(formatLibraryTitle('CODING FOR BEGINNERS USING PYTHON')).toBe('Coding For Beginners Using Python')
  })
})

describe('dedupeLibraryBooks', () => {
  it('keeps the first row per normalized title', () => {
    const items = [book('a', 'Same Title'), book('b', 'same title')]
    expect(dedupeLibraryBooks(items).map((row) => row.id)).toEqual(['a'])
  })
})
