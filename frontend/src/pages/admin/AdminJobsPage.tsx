import type { ChangeEvent, FormEvent } from 'react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Card, CardHeader } from '@/components/common/Card'
import {
  ErrorState,
  LoadingState,
  PracticeTabs,
  SuccessState,
} from '@/components/practice-workspace/PracticeWorkspace'
import {
  archiveAdminJob,
  confirmJobImport,
  createAdminJob,
  fetchAdminImportErrors,
  fetchAdminImportRuns,
  fetchAdminJobs,
  fetchAdminJobSources,
  validateJobImport,
} from '@/services/jobService'
import type { ImportPreviewResponse, JobCard } from '@/types/job'

const inputClass =
  'mt-1 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)]'

export function AdminJobsPage() {
  const queryClient = useQueryClient()
  const [tab, setTab] = useState('jobs')
  const [statusFilter, setStatusFilter] = useState('')

  const [title, setTitle] = useState('')
  const [company, setCompany] = useState('')
  const [description, setDescription] = useState('')

  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null)
  const [uploadFilename, setUploadFilename] = useState('')
  const [selectedRunErrors, setSelectedRunErrors] = useState<string | null>(null)

  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ['admin-jobs', statusFilter],
    queryFn: () => fetchAdminJobs({ status: statusFilter || undefined }),
    enabled: tab === 'jobs',
  })

  const { data: sources, isLoading: sourcesLoading } = useQuery({
    queryKey: ['admin-job-sources'],
    queryFn: fetchAdminJobSources,
    enabled: tab === 'sources',
  })

  const { data: imports, isLoading: importsLoading } = useQuery({
    queryKey: ['admin-job-imports'],
    queryFn: fetchAdminImportRuns,
    enabled: tab === 'imports',
  })

  const { data: importErrors, isLoading: errorsLoading } = useQuery({
    queryKey: ['admin-import-errors', selectedRunErrors],
    queryFn: () => fetchAdminImportErrors(selectedRunErrors!),
    enabled: Boolean(selectedRunErrors),
  })

  const createMutation = useMutation({
    mutationFn: createAdminJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-jobs'] })
      setTitle('')
      setCompany('')
      setDescription('')
    },
  })

  const archiveMutation = useMutation({
    mutationFn: archiveAdminJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-jobs'] }),
  })

  const validateMutation = useMutation({
    mutationFn: validateJobImport,
    onSuccess: (result, file) => {
      setPreview(result)
      setUploadFilename(file.name)
    },
  })

  const confirmMutation = useMutation({
    mutationFn: confirmJobImport,
    onSuccess: () => {
      setPreview(null)
      setUploadFilename('')
      queryClient.invalidateQueries({ queryKey: ['admin-job-imports'] })
      queryClient.invalidateQueries({ queryKey: ['admin-jobs'] })
    },
  })

  const onCreate = (e: FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !company.trim() || description.trim().length < 10) return
    createMutation.mutate({
      title: title.trim(),
      company_name: company.trim(),
      description: description.trim(),
    })
  }

  const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) validateMutation.mutate(file)
    e.target.value = ''
  }

  const onConfirmImport = () => {
    if (!preview?.run_id) return
    confirmMutation.mutate({
      preview_id: preview.run_id,
      filename: uploadFilename || null,
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Jobs admin</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Manage job postings, CSV imports, and ingestion sources.
        </p>
      </div>

      <PracticeTabs
        tabs={[
          { id: 'jobs', label: 'Jobs' },
          { id: 'imports', label: 'Imports' },
          { id: 'sources', label: 'Sources' },
        ]}
        value={tab}
        onChange={setTab}
      />

      {tab === 'jobs' && (
        <div className="space-y-6">
          <Card>
            <CardHeader title="Create job" />
            <form onSubmit={onCreate} className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="text-xs text-[var(--color-text-muted)]">Title</label>
                <input className={inputClass} value={title} onChange={(e) => setTitle(e.target.value)} />
              </div>
              <div>
                <label className="text-xs text-[var(--color-text-muted)]">Company</label>
                <input className={inputClass} value={company} onChange={(e) => setCompany(e.target.value)} />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs text-[var(--color-text-muted)]">Description</label>
                <textarea
                  className={inputClass}
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <Button type="submit" variant="primary" disabled={createMutation.isPending}>
                Create
              </Button>
            </form>
          </Card>

          <Card>
            <CardHeader
              title="Job listings"
              action={
                <select
                  className="rounded-md border border-[var(--color-border)] px-2 py-1 text-xs"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="">All statuses</option>
                  <option value="active">Active</option>
                  <option value="expired">Expired</option>
                  <option value="archived">Archived</option>
                </select>
              }
            />
            {jobsLoading ? (
              <LoadingState label="Loading jobs" />
            ) : jobsData && jobsData.items.length > 0 ? (
              <div className="space-y-2">
                {jobsData.items.map((job: JobCard) => (
                  <div
                    key={job.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--color-border)] p-3"
                  >
                    <div>
                      <Link to={`/jobs/${job.slug}`} className="text-sm font-medium hover:underline">
                        {job.title}
                      </Link>
                      <p className="text-xs text-[var(--color-text-muted)]">{job.company_name}</p>
                      <Badge className="mt-1">{job.status}</Badge>
                    </div>
                    {job.status !== 'archived' && (
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => archiveMutation.mutate(job.id)}
                        disabled={archiveMutation.isPending}
                      >
                        Archive
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-[var(--color-text-muted)]">No jobs found.</p>
            )}
          </Card>
        </div>
      )}

      {tab === 'imports' && (
        <div className="space-y-6">
          <Card>
            <CardHeader title="CSV import" description="Validate then confirm to ingest jobs." />
            <div className="space-y-3">
              <input type="file" accept=".csv,text/csv" onChange={onFileChange} />
              {validateMutation.isPending && <LoadingState label="Validating CSV" />}
              {validateMutation.isError && (
                <ErrorState message="CSV validation failed. Check file format and try again." />
              )}
              {preview && (
                <div className="space-y-3">
                  <div className="flex flex-wrap gap-2 text-sm">
                    <Badge variant="success">{preview.create_count} new</Badge>
                    <Badge variant="accent">{preview.update_count} updates</Badge>
                    <Badge>{preview.duplicate_count} duplicates</Badge>
                    <Badge variant="warning">{preview.error_count} errors</Badge>
                  </div>
                  <div className="max-h-64 overflow-auto rounded-md border border-[var(--color-border)]">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[var(--color-surface-muted)]">
                        <tr>
                          <th className="p-2">Row</th>
                          <th className="p-2">Title</th>
                          <th className="p-2">Company</th>
                          <th className="p-2">Action</th>
                          <th className="p-2">Errors</th>
                        </tr>
                      </thead>
                      <tbody>
                        {preview.rows.map((row) => (
                          <tr key={row.row_number} className="border-t border-[var(--color-border)]">
                            <td className="p-2">{row.row_number}</td>
                            <td className="p-2">{row.title}</td>
                            <td className="p-2">{row.company}</td>
                            <td className="p-2">{row.action}</td>
                            <td className="p-2 text-red-600">{row.errors.join(', ')}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <Button
                    type="button"
                    variant="primary"
                    onClick={onConfirmImport}
                    disabled={!preview.run_id || confirmMutation.isPending}
                  >
                    Confirm import
                  </Button>
                </div>
              )}
              {confirmMutation.isSuccess && (
                <SuccessState title="Import completed">
                  Created {confirmMutation.data.records_created}, updated{' '}
                  {confirmMutation.data.records_updated}, skipped{' '}
                  {confirmMutation.data.records_skipped}, failed{' '}
                  {confirmMutation.data.records_failed}.
                </SuccessState>
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="Import history" />
            {importsLoading ? (
              <LoadingState label="Loading imports" />
            ) : imports && imports.length > 0 ? (
              <div className="space-y-2">
                {imports.map((run) => (
                  <div
                    key={run.id}
                    className="rounded-md border border-[var(--color-border)] p-3 text-sm"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="font-medium">{run.source_file_name ?? 'CSV import'}</p>
                        <p className="text-xs text-[var(--color-text-muted)]">
                          {new Date(run.started_at).toLocaleString()} · {run.source_name ?? 'import'}
                        </p>
                      </div>
                      <Badge>{run.status}</Badge>
                    </div>
                    <p className="mt-1 text-xs text-[var(--color-text-subtle)]">
                      +{run.records_created} / ~{run.records_updated} / skip {run.records_skipped} /
                      fail {run.records_failed}
                    </p>
                    {run.records_failed > 0 && (
                      <Button
                        type="button"
                        size="sm"
                        className="mt-2"
                        onClick={() =>
                          setSelectedRunErrors(
                            selectedRunErrors === run.id ? null : run.id,
                          )
                        }
                      >
                        {selectedRunErrors === run.id ? 'Hide errors' : 'View errors'}
                      </Button>
                    )}
                    {selectedRunErrors === run.id && (
                      <div className="mt-2">
                        {errorsLoading ? (
                          <LoadingState label="Loading errors" />
                        ) : importErrors && importErrors.length > 0 ? (
                          <ul className="space-y-1 text-xs text-red-700">
                            {importErrors.map((err) => (
                              <li key={err.id}>
                                Row {err.row_number}: {err.message}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-xs text-[var(--color-text-muted)]">No error details.</p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-[var(--color-text-muted)]">No import runs yet.</p>
            )}
          </Card>
        </div>
      )}

      {tab === 'sources' && (
        <Card>
          <CardHeader title="Job sources" />
          {sourcesLoading ? (
            <LoadingState label="Loading sources" />
          ) : sources && sources.length > 0 ? (
            <div className="space-y-2">
              {sources.map((source) => (
                <div
                  key={source.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--color-border)] p-3 text-sm"
                >
                  <div>
                    <p className="font-medium">{source.name}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">{source.slug}</p>
                  </div>
                  <div className="flex gap-1">
                    <Badge>{source.source_type}</Badge>
                    <Badge variant={source.is_active ? 'success' : 'default'}>
                      {source.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--color-text-muted)]">No sources configured.</p>
          )}
        </Card>
      )}
    </div>
  )
}
