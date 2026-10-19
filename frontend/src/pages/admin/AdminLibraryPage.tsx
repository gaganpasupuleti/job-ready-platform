import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { EmptyState, ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { sectionStaleMessage, sectionUnavailable } from '@/features/dashboard/overviewModel'
import { useAuth } from '@/hooks/useAuth'
import { sourceChoice, uploadPhase, validatePdfFile, type UploadPhase } from '@/features/library/uploadModel'
import {
  createAdminBook,
  fetchAdminBooks,
  removeAdminPdf,
  updateAdminBook,
  uploadAdminPdf,
  type AdminBook,
  type BookDraft,
  type BookPublication,
} from '@/services/libraryService'

const MAX_PDF_BYTES = 20 * 1024 * 1024

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
  const fileRef = useRef<HTMLInputElement>(null)
  const [pdfName, setPdfName] = useState<string | null>(null)
  const [phase, setPhase] = useState<UploadPhase>('idle')
  const [hasFile, setHasFile] = useState(false)

  function selectedFile() {
    return fileRef.current?.files?.[0] ?? null
  }

  function clearSelectedFile() {
    if (fileRef.current) fileRef.current.value = ''
    setPdfName(null)
  }
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
      external_url: book.external_url ?? '',
      status: book.status,
    })
    clearSelectedFile()
    setHasFile(book.has_file)
    setPhase('idle')
  }

  function resetForm() {
    setEditingId(null)
    setDraft(EMPTY)
    clearSelectedFile()
    setHasFile(false)
    setPhase('idle')
    setFormError('')
  }

  async function save() {
    setFormError('')
    if (!draft.title.trim() || !draft.author.trim() || !draft.category.trim()) {
      setFormError('Enter a title, author, and category.')
      return
    }
    const pdfFile = selectedFile()
    const choice = sourceChoice(draft.external_url, pdfFile?.name ?? pdfName, hasFile)
    if (choice.exclusiveError) {
      setFormError(choice.exclusiveError)
      return
    }
    if (!editingId && choice.needsSource) {
      setFormError('Choose either an https link or a PDF.')
      return
    }
    if (pdfFile) {
      const fileError = validatePdfFile(pdfFile.name, pdfFile.type, pdfFile.size, MAX_PDF_BYTES)
      if (fileError) {
        setFormError(fileError)
        return
      }
    }
    if (choice.link && !draft.external_url.trim().toLowerCase().startsWith('https://')) {
      setFormError('Only https links are allowed.')
      return
    }
    setSaving(true)
    setPhase(pdfFile ? uploadPhase(phase, 'start') : phase)
    try {
      const metadata = { ...draft, external_url: pdfFile ? '' : draft.external_url, status: pdfFile && !editingId ? 'draft' : draft.status }
      const saved = editingId ? await updateAdminBook(editingId, metadata) : await createAdminBook(metadata)
      if (pdfFile) {
        await uploadAdminPdf(saved.id, pdfFile)
        if (!editingId && draft.status !== 'draft') await updateAdminBook(saved.id, draft)
      }
      setPhase(uploadPhase('uploading', 'success'))
      resetForm()
      await queryClient.invalidateQueries({ queryKey: ['admin-library', user?.id] })
    } catch (error) {
      setPhase(uploadPhase('uploading', 'fail'))
      setFormError(error instanceof Error ? error.message : 'Could not save this resource.')
    } finally {
      setSaving(false)
    }
  }

  async function replacePdf() {
    const pdfFile = selectedFile()
    if (!editingId || !pdfFile) {
      setFormError('Choose a .pdf file.')
      return
    }
    const fileError = validatePdfFile(pdfFile.name, pdfFile.type, pdfFile.size, MAX_PDF_BYTES)
    if (fileError) {
      setFormError(fileError)
      return
    }
    setFormError('')
    setPhase(uploadPhase(phase, 'start'))
    try {
      const saved = await uploadAdminPdf(editingId, pdfFile)
      setHasFile(saved.has_file)
      setDraft({ ...draft, external_url: '' })
      clearSelectedFile()
      setPhase(uploadPhase('uploading', 'success'))
      await queryClient.invalidateQueries({ queryKey: ['admin-library', user?.id] })
    } catch (error) {
      setPhase(uploadPhase('uploading', 'fail'))
      setFormError(error instanceof Error ? error.message : 'Could not replace the PDF.')
    }
  }

  async function removePdf() {
    if (!editingId) return
    setFormError('')
    setPhase(uploadPhase(phase, 'start'))
    try {
      const saved = await removeAdminPdf(editingId)
      setHasFile(saved.has_file)
      clearSelectedFile()
      setPhase(uploadPhase('uploading', 'success'))
      await queryClient.invalidateQueries({ queryKey: ['admin-library', user?.id] })
    } catch (error) {
      setPhase(uploadPhase('uploading', 'fail'))
      setFormError(error instanceof Error ? error.message : 'Could not remove the PDF.')
    }
  }

  return (
    <div className="min-w-0 space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-[var(--color-text)]">Library metadata</h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Upload one private PDF or save an https link. The bucket is not public, and the object key is not shown to students.
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
            onChange={(external_url) => {
              setDraft({ ...draft, external_url })
              if (external_url.trim()) clearSelectedFile()
            }}
          />
          <label className="text-sm">
            <span className="mb-1 block text-xs text-[var(--color-text-muted)]">PDF file</span>
            <input
              ref={fileRef}
              aria-label="PDF file"
              type="file"
              accept="application/pdf,.pdf"
              className="block w-full text-sm"
              onChange={(event) => {
                const next = event.target.files?.[0] ?? null
                setPdfName(next?.name ?? null)
                if (next) setDraft({ ...draft, external_url: '' })
              }}
            />
          </label>
          {hasFile ? <p className="text-sm text-[var(--color-text-muted)]">Private PDF attached</p> : null}
          {phase === 'uploading' ? <p className="text-sm text-[var(--color-text-muted)]">Uploading PDF…</p> : null}
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
            {editingId && hasFile ? (
              <Button type="button" variant="secondary" size="sm" onClick={() => void replacePdf()} disabled={phase === 'uploading'}>
                Replace PDF
              </Button>
            ) : null}
            {editingId && hasFile ? (
              <Button type="button" variant="secondary" size="sm" onClick={() => void removePdf()} disabled={phase === 'uploading'}>
                Remove PDF
              </Button>
            ) : null}
            {editingId ? (
              <Button type="button" variant="secondary" size="sm" onClick={resetForm}>
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
                  {book.author} · {book.category} · {book.has_file ? 'PDF' : 'Link'} · {book.status}
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
