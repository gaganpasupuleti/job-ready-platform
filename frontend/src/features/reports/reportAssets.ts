import type { PowerBiReport } from '@/config/powerBiReports'

export function reportAssetUrl(path: string): string {
  const trimmed = path.trim()
  if (!trimmed) return ''
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) return trimmed
  return trimmed.startsWith('/') ? trimmed : `/${trimmed}`
}

export function reportPreviewUrl(report: PowerBiReport): string {
  return reportPreviewCandidates(report)[0] ?? ''
}

/** PDF/image URLs to try for preview (first match wins). */
export function reportPreviewCandidates(report: PowerBiReport): string[] {
  const urls: string[] = []
  if (report.previewImageUrl?.trim()) urls.push(reportAssetUrl(report.previewImageUrl))
  if (report.previewPdfUrl?.trim()) urls.push(reportAssetUrl(report.previewPdfUrl))
  for (const alt of report.previewPdfAlternates ?? []) {
    if (alt.trim()) urls.push(reportAssetUrl(alt))
  }
  return [...new Set(urls)]
}

export function reportDownloadUrl(report: PowerBiReport): string {
  const raw = report.downloadPdfUrl || report.previewPdfUrl
  return raw ? reportAssetUrl(raw) : ''
}

export function reportHasPreview(report: PowerBiReport): boolean {
  return Boolean(report.previewPdfUrl?.trim() || report.previewImageUrl?.trim())
}

export function reportHasDownload(report: PowerBiReport): boolean {
  return Boolean((report.downloadPdfUrl || report.previewPdfUrl)?.trim())
}

export function reportIsAvailable(report: PowerBiReport): boolean {
  return Boolean(report.embedUrl?.trim() || reportHasPreview(report))
}
