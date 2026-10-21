import { Link } from 'react-router-dom'
import { BarChart3, Download, ExternalLink, Eye, Layers } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { powerBiReports } from '@/config/powerBiReports'
import {
  reportDownloadUrl,
  reportHasDownload,
  reportHasPreview,
  reportIsAvailable,
} from '@/features/reports/reportAssets'

export function PowerBiReportsPage() {
  const available = powerBiReports.filter(reportIsAvailable)
  const needsSetup = powerBiReports.filter((report) => !reportIsAvailable(report))

  return (
    <div className="min-w-0 space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-lg font-semibold text-[var(--color-text)]">
            <BarChart3 size={20} className="text-[var(--color-accent)]" aria-hidden />
            Power BI reports
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-[var(--color-text-muted)]">
            Preview exported PDF snapshots in-app, download copies, or open a live Power BI embed when configured.
          </p>
        </div>
        {available.length > 0 ? (
          <div className="shrink-0 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-center sm:min-w-[10rem] sm:text-right">
            <p className="text-2xl font-semibold tabular-nums leading-none text-[var(--color-text)]">{available.length}</p>
            <p className="mt-1 text-[11px] font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
              Reports
            </p>
          </div>
        ) : null}
      </header>

      {powerBiReports.length > 0 ? (
        <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {powerBiReports.map((report) => (
            <li key={report.id}>
              <Card className="flex h-full flex-col">
                <CardHeader title={report.title} description={report.description} />
                <p className="px-4 text-xs font-medium text-[var(--color-text-muted)]">{report.category}</p>
                <div className="mt-auto flex flex-wrap gap-2 p-4 pt-3">
                  {report.labPath ? (
                    <Link to={`/reports/${report.id}/lab`}>
                      <Button type="button" variant="primary" size="sm">
                        <Layers size={14} aria-hidden />
                        Build lab
                      </Button>
                    </Link>
                  ) : null}
                  {reportHasPreview(report) ? (
                    <Link to={`/reports/${report.id}/preview`}>
                      <Button type="button" variant={report.labPath ? 'secondary' : 'primary'} size="sm">
                        <Eye size={14} aria-hidden />
                        Preview
                      </Button>
                    </Link>
                  ) : null}
                  {reportHasDownload(report) ? (
                    <a href={reportDownloadUrl(report)} download>
                      <Button type="button" variant="secondary" size="sm">
                        <Download size={14} aria-hidden />
                        Download
                      </Button>
                    </a>
                  ) : null}
                  {report.embedUrl ? (
                    <Link to={`/reports/${report.id}`}>
                      <Button type="button" variant="secondary" size="sm">Live dashboard</Button>
                    </Link>
                  ) : null}
                </div>
              </Card>
            </li>
          ))}
        </ul>
      ) : null}

      {needsSetup.length > 0 && available.length === 0 ? (
        <Card className="min-w-0">
          <CardHeader
            title="Add a PDF export or embed URL"
            description="Export from Power BI Desktop (PDF) or publish for a live embed."
          />
          <ol className="list-decimal space-y-2 px-4 pb-4 text-sm text-[var(--color-text-muted)]">
            <li>
              <strong className="font-medium text-[var(--color-text)]">Preview / download:</strong> File → Export → PDF,
              save as <code className="text-xs">frontend/public/reports/executive-sales-toast.pdf</code>
            </li>
            <li>
              <strong className="font-medium text-[var(--color-text)]">Live dashboard (optional):</strong> publish to
              Power BI and set <code className="text-xs">VITE_POWERBI_EXECUTIVE_SALES_EMBED_URL</code>
            </li>
          </ol>
        </Card>
      ) : null}

      <p className="text-xs text-[var(--color-text-muted)]">
        PDF previews are static exports; live embeds use Microsoft Power BI.{' '}
        <a
          href="https://learn.microsoft.com/power-bi/developer/embedded/embed-sample-for-customers"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-[var(--color-accent)] hover:underline"
        >
          Embedding guide <ExternalLink size={12} aria-hidden />
        </a>
      </p>
    </div>
  )
}
