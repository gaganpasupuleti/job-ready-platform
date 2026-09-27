import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { EmptyState, ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { sectionStaleMessage, sectionUnavailable } from '@/features/dashboard/overviewModel'
import { useAuth } from '@/hooks/useAuth'
import {
  createAdminBook,
  fetchAdminBooks,
  updateAdminBook,
  type AdminBook,
  type BookDraft,
  type BookPublication,
} from '@/services/libraryService'

const EMPTY: BookDraft = {
  title: '',
  author: '',
  description: '',
  category: '',
  external_url: '',
  status: 'draft',
}

function online() {
  return typeof navigator === 'undefined' ? true : navigator.onLine
}

export function AdminLibraryPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState<BookDraft>(EMPTY)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)
  const books = useQuery({
    queryKey: ['admin-library', user?.id],
    queryFn: fetchAdminBooks,
    enabled: Boolean(user?.id),
  })
  const missing = sectionUnavailable(books)
  const stale = sectionStaleMessage(books, online())

  function edit(book: AdminBook) {
    setEditingId(book.id)
    setFormError('')
    setDraft({
      title: book.title,
      author: book.author,
      description: book.description,
      category: book.category,
      external_url: book.external_url,
      status: book.status,
    })
  }

  async function save() {
    setFormError('')
    if (!draft.title.trim() || !draft.author.trim() || !draft.category.trim()) {
      setFormError('Enter a title, author, and category.')
      return
    }
    if (!draft.external_url.trim().toLowerCase().startsWith('https://')) {
      setFormError('Only https links are allowed.')
      return
    }
    setSaving(true)
    try {
      if (editingId) await updateAdminBook(editingId, draft)
      else await createAdminBook(draft)
      setDraft(EMPTY)
      setEditingId(null)
      await queryClient.invalidateQueries({ queryKey: ['admin-library', user?.id] })
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Could not save this resource.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-w-0 space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-[var(--color-text)]">Library metadata</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          External https links only. Use a clearly identified local test URL. This does not upload a file.
        </p>
      </div>
      <Card className="min-w-0">
        <CardHeader title={editingId ? 'Edit resource' : 'New resource'} />
        <div className="grid gap-3">
          <Field label="Title" value={draft.title} onChange={(title) => setDraft({ ...draft, title })} />
          <Field label="Author" value={draft.author} onChange={(author) => setDraft({ ...draft, author })} />
          <label className="text-sm">
            <span className="mb-1 block text-xs text-[var(--color-text-muted)]">Description</span>
            <textarea
              value={draft.description}
              onChange={(event) => setDraft({ ...draft, description: event.target.value })}
              rows={3}
              className="w-full min-w-0 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            />
          </label>
          <Field label="Category" value={draft.category} onChange={(category) => setDraft({ ...draft, category })} />
          <Field
            label="External https URL"
            value={draft.external_url}
            onChange={(external_url) => setDraft({ ...draft, external_url })}
          />
          <label className="text-sm">
            <span className="mb-1 block text-xs text-[var(--color-text-muted)]">Status</span>
            <select
              value={draft.status}
              onChange={(event) => setDraft({ ...draft, status: event.target.value as BookPublication })}
              className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
          </label>
          {formError ? <ErrorState message={formError} /> : null}
          <div className="flex flex-wrap gap-2">
            <Button type="button" size="sm" onClick={() => void save()} disabled={saving}>
              {editingId ? 'Save changes' : 'Create resource'}
            </Button>
            {editingId ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => {
                  setEditingId(null)
                  setDraft(EMPTY)
                  setFormError('')
                }}
              >
                Cancel edit
              </Button>
            ) : null}
          </div>
        </div>
      </Card>
      <Card className="min-w-0">
        <CardHeader title="All resources" description="Draft and archived links are not shown to students." />
        {books.isPending && books.isFetching && books.data == null ? (
          <p className="text-sm text-[var(--color-text-muted)]">Loading resources</p>
        ) : null}
        {missing ? (
          <div className="space-y-3">
            <ErrorState message="Resources could not be loaded." />
            <Button type="button" variant="secondary" size="sm" onClick={() => void books.refetch()}>
              Retry
            </Button>
          </div>
        ) : null}
        {stale ? (
          <div className="mb-3 space-y-3">
            <ErrorState message={stale} />
            <Button type="button" variant="secondary" size="sm" onClick={() => void books.refetch()}>
              Retry
            </Button>
          </div>
        ) : null}
        {books.data && books.data.length === 0 ? <EmptyState title="No library resources yet" /> : null}
        {books.data && books.data.length > 0 ? (
          <ul className="space-y-2">
            {books.data.map((book) => (
              <li key={book.id} className="min-w-0 rounded-md border border-[var(--color-border)] p-3">
                <p className="break-words text-sm font-medium text-[var(--color-text)]">{book.title}</p>
                <p className="break-words text-xs text-[var(--color-text-muted)]">
                  {book.author} · {book.category} · {book.status}
                </p>
                <button type="button" className="mt-2 text-sm text-[var(--color-accent)] hover:underline" onClick={() => edit(book)}>
                  Edit
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </Card>
    </div>
  )
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="min-w-0 text-sm">
      <span className="mb-1 block text-xs text-[var(--color-text-muted)]">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full min-w-0 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
      />
    </label>
  )
}
