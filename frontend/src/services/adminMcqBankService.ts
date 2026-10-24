import { apiClient } from '@/api/client'

export type McqImportMode = 'add_update' | 'replace_bank'

export interface McqStageUploadResponse {
  import_run_id: string
  bank_key: string
  import_mode: McqImportMode
  workbook_checksum: string
  bank_version_at_preview: number
  can_publish: boolean
  preview: {
    added: Array<{ content_key: string; row: number }>
    updated: Array<{ content_key: string; row: number }>
    unchanged: Array<{ content_key: string; row: number }>
    archived: Array<{ content_key: string }>
    invalid_cross_bank: Array<{ content_key: string; row: number }>
    can_publish: boolean
    blocking_reasons: string[]
  }
  errors: Array<{ sheet: string; row: number; column: string; message: string }>
}

export async function downloadMcqTemplate(bankKey: string): Promise<Blob> {
  const response = await apiClient.get(`/api/v1/admin/mcq-bank/template`, {
    params: { bank_key: bankKey },
    responseType: 'blob',
  })
  return response.data
}

export async function stageMcqImport(
  bankKey: string,
  importMode: McqImportMode,
  file: File,
  allowEmptyReplace = false,
): Promise<McqStageUploadResponse> {
  const form = new FormData()
  form.append('bank_key', bankKey)
  form.append('import_mode', importMode)
  form.append('allow_empty_replace', String(allowEmptyReplace))
  form.append('file', file)
  const response = await apiClient.post<McqStageUploadResponse>(
    '/api/v1/admin/mcq-bank/import/stage',
    form,
  )
  return response.data
}

export async function publishMcqImport(importRunId: string) {
  const response = await apiClient.post('/api/v1/admin/mcq-bank/import/publish', {
    import_run_id: importRunId,
  })
  return response.data
}

export async function fetchMcqImportHistory(bankKey?: string) {
  const response = await apiClient.get('/api/v1/admin/mcq-bank/import/history', {
    params: bankKey ? { bank_key: bankKey } : undefined,
  })
  return response.data
}

export async function exportMcqBank(bankKey: string): Promise<Blob> {
  const response = await apiClient.get('/api/v1/admin/mcq-bank/export', {
    params: { bank_key: bankKey },
    responseType: 'blob',
  })
  return response.data
}
