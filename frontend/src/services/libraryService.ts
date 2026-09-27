import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export type ReadingStatus = 'not_started' | 'reading' | 'completed'
export type BookPublication = 'draft' | 'published' | 'archived'

export type StudentBook = {
  id: string
  title: string
  author: string
  description: string
  category: string
  available: boolean
  external_url: string | null
  bookmarked: boolean
  reading_status: ReadingStatus | null
}

export type StudentBookPage = {
  items: StudentBook[]
  categories: string[]
}

export type AdminBook = {
  id: string
  title: string
  author: string
  description: string
  category: string
  external_url: string
  status: BookPublication
}

export type BookDraft = {
  title: string
  author: string
  description: string
  category: string
  external_url: string
  status: BookPublication
}

export async function fetchLibraryBooks(query: string, category: string) {
  const { data } = await apiClient.get<StudentBookPage>(apiEndpoints.library.books, {
    params: { q: query || undefined, category: category || undefined },
  })
  return data
}

export async function fetchSavedBooks() {
  const { data } = await apiClient.get<StudentBook[]>(apiEndpoints.library.saved)
  return data
}

export async function fetchLibraryBook(id: string) {
  const { data } = await apiClient.get<StudentBook>(apiEndpoints.library.book(id))
  return data
}

export async function bookmarkBook(id: string) {
  const { data } = await apiClient.post<StudentBook>(apiEndpoints.library.bookmark(id))
  return data
}

export async function unbookmarkBook(id: string) {
  const { data } = await apiClient.delete<StudentBook>(apiEndpoints.library.bookmark(id))
  return data
}

export async function setReadingStatus(id: string, status: ReadingStatus) {
  const { data } = await apiClient.put<StudentBook>(apiEndpoints.library.readingStatus(id), { status })
  return data
}

export async function fetchAdminBooks() {
  const { data } = await apiClient.get<AdminBook[]>(apiEndpoints.library.adminBooks)
  return data
}

export async function createAdminBook(payload: BookDraft) {
  const { data } = await apiClient.post<AdminBook>(apiEndpoints.library.adminBooks, payload)
  return data
}

export async function updateAdminBook(id: string, payload: BookDraft) {
  const { data } = await apiClient.patch<AdminBook>(apiEndpoints.library.adminBook(id), payload)
  return data
}
