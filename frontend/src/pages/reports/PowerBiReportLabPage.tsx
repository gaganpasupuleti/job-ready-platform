import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Download,
  Layers,
  PanelLeft,
  PanelRight,
  RotateCcw,
  ZoomIn,
} from 'lucide-react'

import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import { SafeMarkdown } from '@/components/learn/SafeMarkdown'
import {
  EmptyState,
  ErrorState,
  PracticeProgress,
  PracticeTabs,
} from '@/components/practice-workspace/PracticeWorkspace'
import { getPowerBiReport } from '@/config/powerBiReports'
import { reportAssetUrl } from '@/features/reports/reportAssets'
import type { WorkshopContent, WorkshopStep } from '@/features/reports/powerBiWorkshop/types'
import { useLabProgress } from '@/features/reports/powerBiWorkshop/useLabProgress'
import { workshopToMarkdown } from '@/features/reports/powerBiWorkshop/workshopMarkdown'

type LabView = 'overview' | 'guided' | 'resources' | 'validation'

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`Failed to load ${url}`)
  return response.json() as Promise<T>
}

export function PowerBiReportLabPage() {
  const { reportId = '' } = useParams()
  const report = getPowerBiReport(reportId)
  const labBase = report?.labPath ? reportAssetUrl(report.labPath) : ''
  const [view, setView] = useState<LabView>('overview')
  const [stepIndex, setStepIndex] = useState(0)
  const [outlineOpen, setOutlineOpen] = useState(false)
  const [referenceOpen, setReferenceOpen] = useState(false)
  const [zoomImage, setZoomImage] = useState<string | null>(null)

  const lab = useQuery({
    queryKey: ['report-lab-workshop', reportId, labBase],
    queryFn: async () => {
      const [workshop, manifest] = await Promise.all([
        fetchJson<WorkshopContent>(`${labBase}/workshop-content.json`),
        fetchJson<{ tables: { name: string; file: string; rows: number }[] }>(`${labBase}/manifest.json`),
      ])
      return { workshop, manifest }
    },
    enabled: Boolean(report && labBase),
    retry: false,
  })

  const workshop = lab.data?.workshop
  const steps = workshop?.steps ?? []
  const stepIds = useMemo(() => steps.map((s) => s.id), [steps])
  const progress = useLabProgress(reportId, workshop?.contentVersion ?? '0', stepIds)

  const activeStep: WorkshopStep | undefined = steps[stepIndex]

  useEffect(() => {
    if (!activeStep) return
    const el = document.getElementById(`lab-step-${activeStep.id}`)
    el?.scrollIntoView({ block: 'nearest' })
  }, [activeStep?.id])

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

  const markdownGuide = workshop ? workshopToMarkdown(workshop) : ''

  return (
    <div className="flex min-h-0 min-w-0 flex-col gap-4">
      <header className="space-y-3">
        <BackLink reportId={report.id} />
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="flex items-center gap-2 text-lg font-semibold text-[var(--color-text)]">
              <Layers size={20} className="text-[var(--color-accent)]" aria-hidden />
              Build lab — {report.title}
            </h1>
            <p className="mt-1 max-w-3xl text-sm text-[var(--color-text-muted)]">
              Rebuild this report in Power BI Desktop from a blank PBIX. Progress saves in this browser only (
              {workshop?.contentVersion ?? '…'}).
            </p>
          </div>
          <PracticeProgress percent={progress.percent} label="Steps complete" />
        </div>
        <div className="flex flex-wrap gap-2">
          <a href={`${labBase}/datasets.zip`} download>
            <Button type="button" variant="primary" size="sm">
              <Download size={14} aria-hidden />
              Datasets (.zip)
            </Button>
          </a>
          <a href={`${labBase}/student-kit.zip`} download>
            <Button type="button" variant="secondary" size="sm">
              <Download size={14} aria-hidden />
              Student kit
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
            <Button type="button" variant="secondary" size="sm">Finished preview (static)</Button>
          </Link>
        </div>
        <PracticeTabs
          tabs={[
            { id: 'overview', label: 'Overview' },
            { id: 'guided', label: 'Guided build' },
            { id: 'resources', label: 'Resources' },
            { id: 'validation', label: 'Final validation' },
          ]}
          value={view}
          onChange={(id) => setView(id as LabView)}
        />
      </header>

      {lab.isLoading ? <p className="text-sm text-[var(--color-text-muted)]" role="status">Loading workshop…</p> : null}
      {lab.isError ? <ErrorState message="Could not load workshop content." /> : null}

      {workshop && view === 'overview' ? (
        <Card>
          <CardHeader title="Learning outcomes" description={workshop.testedDesktopVersion} />
          <ul className="list-disc space-y-1 px-4 pb-4 pl-8 text-sm text-[var(--color-text-muted)]">
            {workshop.learningOutcomes.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <CardHeader title="Prerequisites" />
          <ul className="list-disc space-y-1 px-4 pb-4 pl-8 text-sm text-[var(--color-text-muted)]">
            {workshop.prerequisites.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          {workshop.intentionalDifferences.length ? (
            <>
              <CardHeader title="Intentional differences from reference PBIX" />
              <ul className="space-y-2 px-4 pb-6 text-sm">
                {workshop.intentionalDifferences.map((d) => (
                  <li key={d.topic} className="rounded-md border border-[var(--color-border)] p-2">
                    <span className="font-medium text-[var(--color-text)]">{d.topic}:</span>{' '}
                    <span className="text-[var(--color-text-muted)]">{d.detail}</span>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </Card>
      ) : null}

      {workshop && view === 'guided' ? (
        <div className="flex min-h-[32rem] flex-1 flex-col gap-3 lg:flex-row">
          <aside
            className={`lg:block lg:w-56 lg:shrink-0 ${outlineOpen ? 'block' : 'hidden'}`}
            aria-label="Build outline"
          >
            <div className="rounded-md border border-[var(--color-border)] p-2">
              <div className="mb-2 flex items-center justify-between lg:hidden">
                <span className="text-xs font-semibold uppercase text-[var(--color-text-muted)]">Outline</span>
                <Button type="button" size="sm" variant="secondary" onClick={() => setOutlineOpen(false)}>
                  Close
                </Button>
              </div>
              <OutlineNav
                workshop={workshop}
                stepIndex={stepIndex}
                completed={progress.completed}
                onSelect={setStepIndex}
              />
            </div>
          </aside>

          <div className="flex min-w-0 flex-1 flex-col gap-3">
            <div className="flex gap-2 lg:hidden">
              <Button type="button" size="sm" variant="secondary" onClick={() => setOutlineOpen(true)}>
                <PanelLeft size={14} aria-hidden />
                Outline
              </Button>
              <Button type="button" size="sm" variant="secondary" onClick={() => setReferenceOpen(true)}>
                <PanelRight size={14} aria-hidden />
                Reference
              </Button>
            </div>

            {activeStep ? (
              <StepPanel step={activeStep} labBase={labBase} onZoom={setZoomImage} />
            ) : (
              <EmptyState title="No steps" />
            )}

            <nav
              className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--color-border)] pt-3"
              aria-label="Step navigation"
            >
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={stepIndex <= 0}
                onClick={() => setStepIndex((i) => Math.max(0, i - 1))}
              >
                <ChevronLeft size={14} aria-hidden />
                Previous
              </Button>
              <Button
                type="button"
                variant={progress.completed.has(activeStep?.id ?? '') ? 'primary' : 'secondary'}
                size="sm"
                disabled={!activeStep}
                onClick={() => activeStep && progress.toggleComplete(activeStep.id)}
              >
                {progress.completed.has(activeStep?.id ?? '') ? 'Completed' : 'Mark complete'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={stepIndex >= steps.length - 1}
                onClick={() => setStepIndex((i) => Math.min(steps.length - 1, i + 1))}
              >
                Next
                <ChevronRight size={14} aria-hidden />
              </Button>
            </nav>
          </div>

          <aside
            className={`lg:block lg:w-72 lg:shrink-0 ${referenceOpen ? 'block' : 'hidden'}`}
            aria-label="Expected result"
          >
            <ReferencePanel
              step={activeStep}
              labBase={labBase}
              onClose={() => setReferenceOpen(false)}
              onZoom={setZoomImage}
            />
          </aside>
        </div>
      ) : null}

      {workshop && view === 'resources' ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="Downloads" description="Same files bundled in the student kit." />
            <ul className="divide-y divide-[var(--color-border)] px-4 pb-4 text-sm">
              {workshop.downloads.map((item) => (
                <li key={item.path} className="flex justify-between gap-2 py-2">
                  <span>{item.label}</span>
                  <a href={`${labBase}/${item.path}`} download className="text-[var(--color-accent)] hover:underline">
                    Download
                  </a>
                </li>
              ))}
              <li className="flex justify-between gap-2 py-2">
                <span>Build guide (generated)</span>
                <a
                  href={`data:text/markdown;charset=utf-8,${encodeURIComponent(markdownGuide)}`}
                  download="build-guide.md"
                  className="text-[var(--color-accent)] hover:underline"
                >
                  Download
                </a>
              </li>
            </ul>
          </Card>
          {lab.data?.manifest ? (
            <Card>
              <CardHeader title="Data tables" />
              <ul className="max-h-80 overflow-y-auto px-4 pb-4 text-sm">
                {lab.data.manifest.tables.map((table) => (
                  <li key={table.name} className="flex justify-between py-1">
                    <span>{table.name}</span>
                    <a href={`${labBase}/${table.file}`} download className="text-[var(--color-accent)]">CSV</a>
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}
          {workshop.excludedMeasures.length ? (
            <Card>
              <CardHeader title="Excluded from required build" />
              <ul className="space-y-2 px-4 pb-4 text-xs text-[var(--color-text-muted)]">
                {workshop.excludedMeasures.map((m) => (
                  <li key={m.name}>
                    <span className="font-medium text-[var(--color-text)]">{m.name}</span> — {m.reason}
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}
        </div>
      ) : null}

      {workshop && view === 'validation' ? (
        <Card>
          <CardHeader
            title="Final validation"
            description="Desktop reconstruction required for animation, bookmarks, and exact formatting."
          />
          <div className="space-y-3 px-4 pb-6 text-sm text-[var(--color-text-muted)]">
            <p>
              With all slicers cleared, compare to{' '}
              <code className="text-xs">expected-results.json</code> →{' '}
              <code className="text-xs">displayCurrency</code> (2dp, profit = sales − cost). Units sold
              (Total Orders measure) = 110,402.
            </p>
            <ul className="list-disc space-y-1 pl-5">
              <li>Imports refresh without author Excel paths</li>
              <li>D/W/M field parameter switches trend axis</li>
              <li>Toast shows on product/store/team filters only</li>
              <li>Cost/profit bar is separate from target achievement bar</li>
            </ul>
            <Button type="button" variant="secondary" size="sm" onClick={progress.resetProgress}>
              <RotateCcw size={14} aria-hidden />
              Reset progress on this browser
            </Button>
          </div>
        </Card>
      ) : null}

      {zoomImage ? (
        <button
          type="button"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setZoomImage(null)}
          aria-label="Close zoomed image"
        >
          <img src={zoomImage} alt="" className="max-h-full max-w-full rounded-md" />
        </button>
      ) : null}
    </div>
  )
}

function StepPanel({
  step,
  labBase,
  onZoom,
}: {
  step: WorkshopStep
  labBase: string
  onZoom: (url: string) => void
}) {
  return (
    <article
      id={`lab-step-${step.id}`}
      className="min-w-0 flex-1 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
      aria-labelledby={`${step.id}-title`}
    >
      <p className="text-xs font-semibold uppercase text-[var(--color-accent)]">{step.stageId}</p>
      <h2 id={`${step.id}-title`} className="mt-1 text-base font-semibold text-[var(--color-text)]">
        {step.title}
      </h2>
      <p className="mt-2 text-sm text-[var(--color-text-muted)]">{step.objective}</p>
      {step.verificationStatus !== 'verified' ? (
        <p className="mt-2 text-xs text-amber-700 dark:text-amber-300" role="status">
          Verification: {step.verificationStatus.replace('_', ' ')}
        </p>
      ) : null}
      <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-[var(--color-text)]">
        {step.actions.map((action) => (
          <li key={action}>
            <SafeMarkdown source={action} />
          </li>
        ))}
      </ol>
      {step.dax?.map((block) => (
        <div key={block.name} className="mt-4">
          <p className="text-xs font-semibold text-[var(--color-text)]">{block.table} → {block.name}</p>
          <pre className="mt-1 overflow-x-auto rounded-md bg-[var(--color-surface-muted)] p-3 font-mono text-xs">
            {block.expression.trim()}
          </pre>
        </div>
      ))}
      {step.visual ? (
        <p className="mt-3 text-xs text-[var(--color-text-muted)]">
          Visual: <strong>{step.visual.visualType}</strong> — {step.visual.fields.join(', ') || 'see reference'}
        </p>
      ) : null}
      {step.referenceNotes ? (
        <div className="mt-3 rounded-md border border-dashed border-[var(--color-border)] p-2 text-xs">
          <SafeMarkdown source={step.referenceNotes} />
        </div>
      ) : null}
      {step.commonMistakes.length ? (
        <div className="mt-3">
          <p className="text-xs font-semibold">Common mistakes</p>
          <ul className="list-disc pl-5 text-xs text-[var(--color-text-muted)]">
            {step.commonMistakes.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {step.images[0] ? (
        <button
          type="button"
          className="mt-4 block w-full max-w-xl text-left"
          onClick={() => onZoom(`${labBase}/${step.images[0].src}`)}
        >
          <img
            src={`${labBase}/${step.images[0].src}`}
            alt={step.images[0].alt}
            className="w-full rounded-md border border-[var(--color-border)]"
            loading="lazy"
          />
          <span className="mt-1 inline-flex items-center gap-1 text-xs text-[var(--color-accent)]">
            <ZoomIn size={12} aria-hidden />
            {step.images[0].caption}
          </span>
        </button>
      ) : null}
    </article>
  )
}

function ReferencePanel({
  step,
  labBase,
  onClose,
  onZoom,
}: {
  step?: WorkshopStep
  labBase: string
  onClose: () => void
  onZoom: (url: string) => void
}) {
  if (!step) return null
  const image = step.images[0]
  return (
    <div className="rounded-md border border-[var(--color-border)] p-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--color-text)]">Expected result</h3>
        <Button type="button" size="sm" variant="secondary" className="lg:hidden" onClick={onClose}>
          Close
        </Button>
      </div>
      <p className="text-xs text-[var(--color-text-muted)]">{step.expectedResult}</p>
      {step.verificationChecklist.length ? (
        <ul className="mt-2 space-y-1 text-xs">
          {step.verificationChecklist.map((item) => (
            <li key={item} className="flex gap-2">
              <span aria-hidden>☐</span>
              {item}
            </li>
          ))}
        </ul>
      ) : null}
      {image ? (
        <button type="button" className="mt-3 block w-full" onClick={() => onZoom(`${labBase}/${image.src}`)}>
          <img
            src={`${labBase}/${image.src}`}
            alt={image.alt}
            className="w-full rounded-md border border-[var(--color-border)]"
            loading="lazy"
          />
        </button>
      ) : null}
    </div>
  )
}

function OutlineNav({
  workshop,
  stepIndex,
  completed,
  onSelect,
}: {
  workshop: WorkshopContent
  stepIndex: number
  completed: Set<string>
  onSelect: (index: number) => void
}) {
  let globalIndex = 0
  return (
    <ol className="space-y-3 text-xs">
      {workshop.stages
        .sort((a, b) => a.order - b.order)
        .map((stage) => {
          const stageSteps = workshop.steps.filter((s) => s.stageId === stage.id).sort((a, b) => a.order - b.order)
          return (
            <li key={stage.id}>
              <p className="font-semibold text-[var(--color-text)]">
                {stage.order}. {stage.title}
              </p>
              <ul className="mt-1 space-y-0.5">
                {stageSteps.map((step) => {
                  const idx = globalIndex
                  globalIndex += 1
                  const isCurrent = idx === stepIndex
                  const done = completed.has(step.id)
                  return (
                    <li key={step.id}>
                      <button
                        type="button"
                        onClick={() => onSelect(idx)}
                        className={`w-full rounded px-1 py-0.5 text-left hover:bg-[var(--color-surface-muted)] ${
                          isCurrent ? 'font-medium text-[var(--color-accent)]' : 'text-[var(--color-text-muted)]'
                        }`}
                        aria-current={isCurrent ? 'step' : undefined}
                      >
                        <span aria-hidden>{done ? '✓' : '○'}</span> {step.title}
                      </button>
                    </li>
                  )
                })}
              </ul>
            </li>
          )
        })}
    </ol>
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
