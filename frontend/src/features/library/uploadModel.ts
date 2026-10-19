/** Admin PDF upload rules. A book has a link or a file, not both. */

export type UploadPhase = 'idle' | 'uploading' | 'failed'

export function validatePdfFile(name: string, type: string, size: number, maxBytes: number) {
  if (!name.toLowerCase().endsWith('.pdf')) return 'Choose a .pdf file.'
  const media = type.split(';', 1)[0].trim().toLowerCase()
  if (media && media !== 'application/pdf') return 'Only PDF files can be uploaded.'
  if (size <= 0) return 'The PDF file is empty.'
  if (size > maxBytes) return 'The PDF is too large.'
  return null
}

export function sourceChoice(url: string, fileName: string | null, hasFile: boolean) {
  const link = url.trim().length > 0
  const selected = Boolean(fileName)
  return {
    link,
    selected,
    hasFile,
    exclusiveError: link && selected ? 'Choose either an https link or a PDF.' : null,
    needsSource: !link && !selected && !hasFile,
  }
}

export function uploadPhase(_phase: UploadPhase, event: 'start' | 'success' | 'fail'): UploadPhase {
  if (event === 'start') return 'uploading'
  if (event === 'success') return 'idle'
  return 'failed'
}
