import { apiClient } from '@/api/client'
import { apiEndpoints, AUTH_TOKEN_KEY } from '@/api/config'

export type ReadingStatus = 'not_started' | 'reading' | 'completed'
export type BookPublication = 'draft' | 'published' | 'archived'

export type StudentBook = {
  id: string
  title: string
  author: string
  description: string
  category: string
  available: boolean
  has_file: boolean
  external_url: string | null
  bookmarked: boolean
  reading_status: ReadingStatus | null
  last_page: number | null
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
  external_url: string | null
  has_file: boolean
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
  const { data } = await apiClient.post<AdminBook>(apiEndpoints.library.adminBooks, sourcePayload(payload))
  return data
}

export async function updateAdminBook(id: string, payload: BookDraft) {
  const { data } = await apiClient.patch<AdminBook>(apiEndpoints.library.adminBook(id), sourcePayload(payload))
  return data
}

export async function fetchReadLink(id: string) {
  const { data } = await apiClient.get<{ url: string; expires_in: number }>(apiEndpoints.library.readLink(id))
  return data
}

export async function saveReadingProgress(id: string, lastPage: number) {
  const { data } = await apiClient.put<StudentBook>(apiEndpoints.library.progress(id), { last_page: lastPage })
  return data
}

export async function fetchLibraryFile(url: string) {
  const headers: Record<string, string> = {}
  const token = url.startsWith('/') ? localStorage.getItem(AUTH_TOKEN_KEY) : null
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(url, { headers })
  if (token && token !== localStorage.getItem(AUTH_TOKEN_KEY)) {
    throw new Error('Session changed')
  }
  if (!response.ok) {
    let message = 'This PDF file could not be opened.'
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') message = body.detail
    } catch {
      message = response.status === 404 ? 'This PDF file is missing.' : message
    }
    throw new LibraryFileError(message, response.status)
  }
  return response.arrayBuffer()
}

export async function uploadAdminPdf(id: string, file: File) {
  const body = new FormData()
  body.append('file', file)
  const { data } = await apiClient.post<AdminBook>(apiEndpoints.library.adminFile(id), body, {
    headers: { 'Content-Type': 'multipart/form-data' },
    transformRequest: (payload, headers) => {
      if (headers) delete headers['Content-Type']
      return payload
    },
  })
  return data
}

export async function removeAdminPdf(id: string) {
  const { data } = await apiClient.delete<AdminBook>(apiEndpoints.library.adminFile(id))
  return data
}

export class LibraryFileError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function sourcePayload(draft: BookDraft) {
  const payload: Record<string, string> = {
    title: draft.title.trim(),
    author: draft.author.trim(),
    description: draft.description.trim(),
    category: draft.category.trim(),
    status: draft.status,
  }
  if (draft.external_url.trim()) payload.external_url = draft.external_url.trim()
  return payload
}
