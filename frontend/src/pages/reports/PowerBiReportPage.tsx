import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, BarChart3 } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { EmptyState } from '@/components/practice-workspace/PracticeWorkspace'
import { getPowerBiReport } from '@/config/powerBiReports'
import { reportDownloadUrl, reportHasPreview } from '@/features/reports/reportAssets'

export function PowerBiReportPage() {
  const { reportId = '' } = useParams()
  const report = getPowerBiReport(reportId)

  if (!report) {
    return (
      <div className="min-w-0 space-y-4">
        <BackLink />
        <EmptyState title="Report not found" description="Choose a report from the Power BI catalog." />
      </div>
    )
  }

  if (!report.embedUrl) {
    return (
      <div className="min-w-0 space-y-4">
        <BackLink />
        <Card className="space-y-3 p-4 text-sm text-[var(--color-text-muted)]">
          <p className="font-medium text-[var(--color-text)]">{report.title}</p>
          <p>No live Power BI embed is configured.</p>
          <div className="flex flex-wrap gap-2">
            {reportHasPreview(report) ? (
              <Link to={`/reports/${report.id}/preview`}>
                <Button type="button" variant="primary" size="sm">PDF preview</Button>
              </Link>
            ) : null}
            {reportDownloadUrl(report) ? (
              <a href={reportDownloadUrl(report)} download>
                <Button type="button" variant="secondary" size="sm">Download PDF</Button>
              </a>
            ) : null}
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex min-h-[min(72vh,900px)] min-w-0 flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <BackLink />
          <h1 className="mt-2 flex items-center gap-2 text-lg font-semibold text-[var(--color-text)]">
            <BarChart3 size={20} className="shrink-0 text-[var(--color-accent)]" aria-hidden />
            <span className="truncate">{report.title}</span>
          </h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">{report.category}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {reportHasPreview(report) ? (
            <Link to={`/reports/${report.id}/preview`}>
              <Button type="button" variant="secondary" size="sm">PDF preview</Button>
            </Link>
          ) : null}
          <a href={report.embedUrl} target="_blank" rel="noreferrer">
            <Button type="button" variant="secondary" size="sm">Open in Power BI</Button>
          </a>
          {reportDownloadUrl(report) ? (
            <a href={reportDownloadUrl(report)} download>
              <Button type="button" variant="secondary" size="sm">Download PDF</Button>
            </a>
          ) : null}
        </div>
      </div>
      <div className="relative min-h-0 flex-1 overflow-hidden rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)]">
        <iframe
          title={report.title}
          src={report.embedUrl}
          className="absolute inset-0 h-full w-full border-0"
          allowFullScreen
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
        />
      </div>
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
