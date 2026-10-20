import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Download, Layers } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { EmptyState, ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { getPowerBiReport } from '@/config/powerBiReports'
import { reportDownloadUrl, reportPreviewCandidates } from '@/features/reports/reportAssets'

async function probePreviewAsset(url: string): Promise<'pdf' | 'image' | 'missing'> {
  const response = await fetch(url, { method: 'GET' })
  if (!response.ok) return 'missing'
  const type = (response.headers.get('content-type') ?? '').toLowerCase()
  if (type.includes('pdf')) return 'pdf'
  if (type.startsWith('image/')) return 'image'
  const bytes = new Uint8Array(await response.arrayBuffer())
  if (bytes.length >= 4 && bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 && bytes[3] === 0x46) {
    return 'pdf'
  }
  if (bytes.length >= 8 && bytes[0] === 0x89 && bytes[1] === 0x50) return 'image'
  return 'missing'
}

export function PowerBiReportPreviewPage() {
  const { reportId = '' } = useParams()
  const report = getPowerBiReport(reportId)
  const candidates = report ? reportPreviewCandidates(report) : []
  const downloadUrl = report ? reportDownloadUrl(report) : ''

  const probe = useQuery({
    queryKey: ['report-preview-probe', reportId, candidates],
    queryFn: async () => {
      for (const url of candidates) {
        const kind = await probePreviewAsset(url)
        if (kind === 'pdf') return { kind: 'pdf' as const, url }
        if (kind === 'image') return { kind: 'image' as const, url }
      }
      return { kind: 'missing' as const, url: '' }
    },
    enabled: Boolean(report && candidates.length > 0),
    retry: false,
  })

  if (!report) {
    return (
      <div className="min-w-0 space-y-4">
        <BackLink />
        <EmptyState title="Report not found" description="Choose a report from the catalog." />
      </div>
    )
  }

  const embedUrl = report.embedUrl?.trim() ?? ''

  const missingHelp = embedUrl ? (
    <iframe
      title={report.title}
      src={embedUrl}
      className="min-h-[min(72vh,900px)] w-full flex-1 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)]"
      allowFullScreen
      loading="lazy"
      referrerPolicy="no-referrer-when-downgrade"
    />
  ) : (
    <EmptyState
      title="Preview not available"
      description="Add executive-sales-toast.png or executive-sales-toast.pdf under frontend/public/reports/, or set VITE_POWERBI_EXECUTIVE_SALES_EMBED_URL for a live dashboard."
    />
  )

  return (
    <div className="flex min-h-[min(72vh,900px)] min-w-0 flex-col gap-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <BackLink />
          <h1 className="mt-2 text-lg font-semibold text-[var(--color-text)]">{report.title}</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">Report preview</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {report.labPath ? (
            <Link to={`/reports/${report.id}/lab`}>
              <Button type="button" variant="primary" size="sm">
                <Layers size={14} aria-hidden />
                Build lab
              </Button>
            </Link>
          ) : null}
          {downloadUrl && probe.data?.kind !== 'missing' ? (
            <a href={downloadUrl} download>
              <Button type="button" variant="secondary" size="sm">
                <Download size={14} aria-hidden />
                Download
              </Button>
            </a>
          ) : null}
        </div>
      </header>

      {probe.isLoading ? <p className="text-sm text-[var(--color-text-muted)]">Loading preview…</p> : null}
      {probe.isError ? <ErrorState message="Preview could not be loaded." /> : null}

      {probe.data?.kind === 'pdf' ? (
        <iframe
          title={report.title}
          src={probe.data.url}
          className="min-h-[min(72vh,900px)] w-full flex-1 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)]"
        />
      ) : null}

      {probe.data?.kind === 'image' ? (
        <div className="overflow-auto rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-4">
          <img src={probe.data.url} alt={`Preview of ${report.title}`} className="mx-auto max-w-full" />
        </div>
      ) : null}

      {probe.data?.kind === 'missing' ? missingHelp : null}
    </div>
  )
}

function BackLink() {
  return (
    <Link
      to="/reports"
      className="inline-flex items-center gap-1 text-sm font-medium text-[var(--color-accent)] hover:underline"
    >
      <ArrowLeft size={16} aria-hidden />
      All reports
    </Link>
  )
}
