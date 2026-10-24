import type { ChangeEvent, FormEvent } from 'react'
import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import {
  downloadMcqTemplate,
  exportMcqBank,
  fetchMcqImportHistory,
  publishMcqImport,
  stageMcqImport,
  type McqImportMode,
  type McqStageUploadResponse,
} from '@/services/adminMcqBankService'

const inputClass =
  'mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm'

export function AdminMcqBankPage() {
  const [bankKey, setBankKey] = useState('phase11-aptitude')
  const [importMode, setImportMode] = useState<McqImportMode>('add_update')
  const [allowEmptyReplace, setAllowEmptyReplace] = useState(false)
  const [staged, setStaged] = useState<McqStageUploadResponse | null>(null)
  const [uploadName, setUploadName] = useState('')

  const { data: history, isLoading: historyLoading, refetch } = useQuery({
    queryKey: ['mcq-import-history', bankKey],
    queryFn: () => fetchMcqImportHistory(bankKey),
  })

  const publishMutation = useMutation({
    mutationFn: () => publishMcqImport(staged!.import_run_id),
    onSuccess: () => {
      setStaged(null)
      refetch()
    },
  })

  const onDownloadTemplate = async () => {
    const blob = await downloadMcqTemplate(bankKey)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `jobready-mcq-${bankKey}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  }

  const onExport = async () => {
    const blob = await exportMcqBank(bankKey)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `jobready-mcq-export-${bankKey}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  }

  const onFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setUploadName(file.name)
    const result = await stageMcqImport(bankKey, importMode, file, allowEmptyReplace)
    setStaged(result)
  }

  const onPublish = (event: FormEvent) => {
    event.preventDefault()
    if (staged?.can_publish) publishMutation.mutate()
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <Card>
        <CardHeader title="MCQ Excel bank" subtitle="Upload, preview, and publish question banks" />
        <form className="space-y-4 p-4" onSubmit={onPublish}>
          <label className="block text-sm">
            Bank key
            <input className={inputClass} value={bankKey} onChange={(e) => setBankKey(e.target.value)} />
          </label>
          <label className="block text-sm">
            Import mode
            <select
              className={inputClass}
              value={importMode}
              onChange={(e) => setImportMode(e.target.value as McqImportMode)}
            >
              <option value="add_update">Add / update (default)</option>
              <option value="replace_bank">Replace selected bank</option>
            </select>
          </label>
          {importMode === 'replace_bank' && (
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={allowEmptyReplace}
                onChange={(e) => setAllowEmptyReplace(e.target.checked)}
              />
              Allow empty replace (archive entire bank)
            </label>
          )}
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" onClick={onDownloadTemplate}>
              Download template
            </Button>
            <Button type="button" variant="secondary" onClick={onExport}>
              Export current bank
            </Button>
          </div>
          <label className="block text-sm">
            Upload workbook (.xlsx)
            <input className={inputClass} type="file" accept=".xlsx" onChange={onFile} />
          </label>
          {uploadName && <p className="text-xs text-[var(--color-text-muted)]">Last file: {uploadName}</p>}
          {staged && (
            <div className="rounded border border-[var(--color-border)] p-3 text-sm">
              <p>Preview — bank version at preview: {staged.bank_version_at_preview}</p>
              <ul className="mt-2 list-disc pl-5">
                <li>Added: {staged.preview.added.length}</li>
                <li>Updated: {staged.preview.updated.length}</li>
                <li>Unchanged: {staged.preview.unchanged.length}</li>
                <li>Archived: {staged.preview.archived.length}</li>
                <li>Invalid: {staged.errors.length}</li>
              </ul>
              {staged.preview.blocking_reasons.length > 0 && (
                <p className="mt-2 text-[var(--color-warning)]">
                  {staged.preview.blocking_reasons.join('; ')}
                </p>
              )}
              {staged.errors.length > 0 && (
                <ul className="mt-2 max-h-40 overflow-auto text-xs text-[var(--color-danger)]">
                  {staged.errors.slice(0, 20).map((err, i) => (
                    <li key={i}>
                      {err.sheet} row {err.row} {err.column}: {err.message}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
          <Button type="submit" disabled={!staged?.can_publish || publishMutation.isPending}>
            Publish valid changes
          </Button>
        </form>
      </Card>
      <Card>
        <CardHeader title="Import history" />
        {historyLoading ? (
          <LoadingState />
        ) : (
          <ul className="divide-y p-4 text-sm">
            {(history ?? []).map((row: { id: string; status: string; created_at: string }) => (
              <li key={row.id} className="py-2">
                {row.created_at} — {row.status} — {row.id}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
