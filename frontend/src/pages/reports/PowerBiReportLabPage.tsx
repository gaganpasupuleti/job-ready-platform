import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Download, Database, FileCode2, GitBranch, Layers } from 'lucide-react'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { SafeMarkdown } from '@/components/learn/SafeMarkdown'
import { EmptyState, ErrorState } from '@/components/practice-workspace/PracticeWorkspace'
import { getPowerBiReport } from '@/config/powerBiReports'
import { reportAssetUrl } from '@/features/reports/reportAssets'

type LabManifest = {
  tables: { name: string; file: string; rows: number }[]
  measureCount: number
  queryCount: number
}

type DaxBlock = { table: string; name: string; expression: string }
type QueryBlock = { table: string; expression: string }
type Relationship = {
  fromTable: string
  fromColumn: string
  toTable: string
  toColumn: string
  cardinality: string
  crossFilter: string
  active: boolean
}
type VisualBlock = {
  id: string
  visualType: string
  title: string
  fields: string[]
  howTo: string
  snip: string
}
type BuildStep = {
  step: number
  id: string
  title: string
  instructions: string
  snip: string
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Failed to load ${url}`)
  return response.json() as Promise<T>
}

export function PowerBiReportLabPage() {
  const { reportId = '' } = useParams()
  const report = getPowerBiReport(reportId)
  const labBase = report?.labPath ? reportAssetUrl(report.labPath) : ''
  const [showAdvancedVisuals, setShowAdvancedVisuals] = useState(false)

  const lab = useQuery({
    queryKey: ['report-lab', reportId, labBase],
    queryFn: async () => {
      const [manifest, measures, queries, relationships, visuals, buildSteps, guideRes, relRes] =
        await Promise.all([
        fetchJson<LabManifest>(`${labBase}/manifest.json`),
        fetchJson<DaxBlock[]>(`${labBase}/dax-measures.json`),
        fetchJson<QueryBlock[]>(`${labBase}/power-query.json`),
        fetchJson<Relationship[]>(`${labBase}/relationships.json`),
        fetchJson<VisualBlock[]>(`${labBase}/visuals.json`),
        fetchJson<BuildStep[]>(`${labBase}/build-steps.json`),
        fetch(`${labBase}/build-guide.md`),
        fetch(`${labBase}/relationships.md`),
      ])
      const guide = guideRes.ok ? await guideRes.text() : ''
      const relationshipsGuide = relRes.ok ? await relRes.text() : ''
      return { manifest, measures, queries, relationships, visuals, buildSteps, guide, relationshipsGuide }
    },
    enabled: Boolean(report && labBase),
    retry: false,
  })

  if (!report) {
    return (
      <div className="min-w-0 space-y-4">
        <BackLink reportId="" />
        <EmptyState title="Report not found" description="Choose a report from the catalog." />
      </div>
    )
  }

  if (!labBase) {
    return (
      <div className="min-w-0 space-y-4">
        <BackLink reportId={report.id} />
        <EmptyState title="Lab not configured" description="This report does not have build blocks yet." />
      </div>
    )
  }

  return (
    <div className="min-w-0 space-y-6">
      <header className="space-y-2">
        <BackLink reportId={report.id} />
        <h1 className="flex items-center gap-2 text-lg font-semibold text-[var(--color-text)]">
          <Layers size={20} className="text-[var(--color-accent)]" aria-hidden />
          Build lab — {report.title}
        </h1>
        <p className="max-w-3xl text-sm text-[var(--color-text-muted)]">
          Work in order: <strong className="text-[var(--color-text)]">relationships → data → build steps → DAX</strong>.
          Each step includes a screenshot of the real report canvas (not the Power BI ribbon).
        </p>
        <div className="flex flex-wrap gap-2">
          <a href={`${labBase}/datasets.zip`} download>
            <Button type="button" variant="primary" size="sm">
              <Download size={14} aria-hidden />
              All datasets (.zip)
            </Button>
          </a>
          {report.sourceFile ? (
            <a href={reportAssetUrl(`/reports/${report.sourceFile}`)} download>
              <Button type="button" variant="secondary" size="sm">
                <Download size={14} aria-hidden />
                Reference .pbix
              </Button>
            </a>
          ) : null}
          <Link to={`/reports/${report.id}/preview`}>
            <Button type="button" variant="secondary" size="sm">Finished preview</Button>
          </Link>
        </div>
      </header>

      {lab.isLoading ? <p className="text-sm text-[var(--color-text-muted)]">Loading lab blocks…</p> : null}
      {lab.isError ? <ErrorState message="Could not load lab assets." /> : null}

      {lab.data ? (
        <>
          <Card>
            <CardHeader
              title="Build path (follow in order)"
              description="Six steps from empty page to toast dashboard — each with a clear screenshot."
            />
            <ol className="space-y-8 px-4 pb-6">
              {lab.data.buildSteps.map((step) => (
                <li key={step.id} className="min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--color-accent)]">
                    Step {step.step}
                  </p>
                  <h3 className="mt-1 text-base font-semibold text-[var(--color-text)]">{step.title}</h3>
                  <img
                    src={`${labBase}/${step.snip}`}
                    alt={step.title}
                    className="mt-3 w-full max-w-4xl rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]"
                    loading="lazy"
                  />
                  <div className="prose prose-sm mt-3 max-w-3xl text-sm text-[var(--color-text-muted)]">
                    <SafeMarkdown source={step.instructions} />
                  </div>
                </li>
              ))}
            </ol>
          </Card>

          <Card>
            <CardHeader
              title="Model relationships"
              description="Do this in Model view before any visuals."
            />
            <ul className="space-y-2 px-4 pb-4 text-sm">
              {lab.data.relationships.map((rel) => (
                <li
                  key={`${rel.fromTable}-${rel.fromColumn}-${rel.toTable}`}
                  className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface-muted)] px-3 py-2"
                >
                  <GitBranch size={12} className="mr-1 inline text-[var(--color-accent)]" aria-hidden />
                  <span className="font-medium text-[var(--color-text)]">{rel.fromTable}</span>
                  <span className="text-[var(--color-text-muted)]">.{rel.fromColumn}</span>
                  <span className="mx-1 text-[var(--color-text-muted)]">→</span>
                  <span className="font-medium text-[var(--color-text)]">{rel.toTable}</span>
                  <span className="text-[var(--color-text-muted)]">.{rel.toColumn}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <CardHeader title="Every visual part (advanced)" description="Optional — only if you need one specific tile." />
            <div className="px-4 pb-4">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setShowAdvancedVisuals((open) => !open)}
              >
                {showAdvancedVisuals ? 'Hide' : 'Show'} {lab.data.visuals.length} parts
              </Button>
              {showAdvancedVisuals ? (
                <ul className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {lab.data.visuals.map((visual) => (
                    <li
                      key={visual.id}
                      className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)]"
                    >
                      <img
                        src={`${labBase}/${visual.snip}`}
                        alt={visual.title}
                        className="h-24 w-full object-contain bg-[var(--color-surface-muted)]"
                        loading="lazy"
                      />
                      <div className="p-2 text-xs">
                        <p className="font-semibold text-[var(--color-text)]">{visual.title}</p>
                        <p className="text-[var(--color-text-muted)]">{visual.visualType}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          </Card>

          <Card>
            <CardHeader
              title="Data tables"
              description={`${lab.data.manifest.tables.length} tables extracted from the model — use as CSV imports.`}
            />
            <ul className="divide-y divide-[var(--color-border)] px-4 pb-4">
              {lab.data.manifest.tables.map((table) => (
                <li key={table.name} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                  <span className="flex items-center gap-2 font-medium text-[var(--color-text)]">
                    <Database size={14} className="text-[var(--color-accent)]" aria-hidden />
                    {table.name}
                    <span className="font-normal text-[var(--color-text-muted)]">({table.rows.toLocaleString()} rows)</span>
                  </span>
                  <a href={`${labBase}/${table.file}`} download className="text-[var(--color-accent)] hover:underline">
                    Download CSV
                  </a>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <CardHeader
              title="Power Query (M)"
              description={`${lab.data.queries.length} queries — repoint Excel paths to the CSV folder above.`}
            />
            <ul className="max-h-[28rem] space-y-3 overflow-y-auto px-4 pb-4">
              {lab.data.queries.map((block) => (
                <li key={block.table}>
                  <p className="text-sm font-semibold text-[var(--color-text)]">{block.table || 'Query'}</p>
                  <pre className="mt-1 overflow-x-auto rounded-md bg-[var(--color-surface-muted)] p-3 font-mono text-xs">
                    {block.expression.trim()}
                  </pre>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <CardHeader
              title="DAX measures"
              description={`${lab.data.measures.length} measures — create in a # Measures table in your model.`}
            />
            <ul className="max-h-[32rem] space-y-3 overflow-y-auto px-4 pb-4">
              {lab.data.measures.map((block) => (
                <li key={`${block.table}-${block.name}`}>
                  <p className="text-sm font-semibold text-[var(--color-text)]">
                    <FileCode2 size={14} className="mr-1 inline text-[var(--color-accent)]" aria-hidden />
                    {block.table} → {block.name}
                  </p>
                  <pre className="mt-1 overflow-x-auto rounded-md bg-[var(--color-surface-muted)] p-3 font-mono text-xs">
                    {block.expression.trim()}
                  </pre>
                </li>
              ))}
            </ul>
          </Card>

          {lab.data.guide ? (
            <section className="reading-shell rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
              <h2 className="mb-3 text-base font-semibold text-[var(--color-text)]">Build flow (full steps)</h2>
              <SafeMarkdown source={lab.data.guide} />
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  )
}

function BackLink({ reportId }: { reportId: string }) {
  const to = reportId ? `/reports/${reportId}` : '/reports'
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-1 text-sm font-medium text-[var(--color-accent)] hover:underline"
    >
      <ArrowLeft size={16} aria-hidden />
      Back to report
    </Link>
  )
}
