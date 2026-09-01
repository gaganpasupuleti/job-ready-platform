import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type {
  AdminJobCreate,
  AdminJobListResponse,
  AdminJobUpdate,
  ApplicationDetail,
  ApplicationStatusChange,
  ApplicationStatusHistoryItem,
  ApplicationSummary,
  ApplicationUpdate,
  ImportConfirmRequest,
  ImportConfirmResponse,
  ImportPreviewResponse,
  IngestionErrorPublic,
  IngestionRunPublic,
  JobDetail,
  JobListFilters,
  JobListResponse,
  JobPreferenceUpdate,
  JobSourcePublic,
  JobsSummary,
  SavedJobItem,
} from '@/types/job'

export async function fetchJobs(filters?: JobListFilters) {
  const { data } = await apiClient.get<JobListResponse>(apiEndpoints.jobs.list, { params: filters })
  return data
}

export async function fetchJobsSummary() {
  const { data } = await apiClient.get<JobsSummary>(apiEndpoints.jobs.summary)
  return data
}

export async function fetchSavedJobs() {
  const { data } = await apiClient.get<SavedJobItem[]>(apiEndpoints.jobs.saved)
  return data
}

export async function fetchRecommendedJobs(limit = 20) {
  const { data } = await apiClient.get<JobListResponse>(apiEndpoints.jobs.recommended, {
    params: { limit },
  })
  return data
}

export async function fetchJob(jobIdOrSlug: string) {
  const { data } = await apiClient.get<JobDetail>(apiEndpoints.jobs.detail(jobIdOrSlug))
  return data
}

export async function saveJob(jobId: string) {
  await apiClient.post(apiEndpoints.jobs.save(jobId))
}

export async function unsaveJob(jobId: string) {
  await apiClient.delete(apiEndpoints.jobs.save(jobId))
}

export async function markJobApplied(jobId: string) {
  const { data } = await apiClient.post<ApplicationDetail>(apiEndpoints.jobs.apply(jobId))
  return data
}

export async function startJobPreparing(jobId: string) {
  const { data } = await apiClient.post<ApplicationDetail>(apiEndpoints.jobs.prepare(jobId))
  return data
}

export async function updateJobPreferences(payload: JobPreferenceUpdate) {
  await apiClient.put(apiEndpoints.jobs.preferences, payload)
}

export async function fetchApplications(status?: string) {
  const { data } = await apiClient.get<ApplicationSummary[]>(apiEndpoints.applications.list, {
    params: status ? { status } : undefined,
  })
  return data
}

export async function fetchApplication(applicationId: string) {
  const { data } = await apiClient.get<ApplicationDetail>(
    apiEndpoints.applications.detail(applicationId),
  )
  return data
}

export async function updateApplication(applicationId: string, payload: ApplicationUpdate) {
  const { data } = await apiClient.patch<ApplicationDetail>(
    apiEndpoints.applications.detail(applicationId),
    payload,
  )
  return data
}

export async function changeApplicationStatus(
  applicationId: string,
  payload: ApplicationStatusChange,
) {
  const { data } = await apiClient.post<ApplicationDetail>(
    apiEndpoints.applications.status(applicationId),
    payload,
  )
  return data
}

export async function fetchApplicationHistory(applicationId: string) {
  const { data } = await apiClient.get<ApplicationStatusHistoryItem[]>(
    apiEndpoints.applications.history(applicationId),
  )
  return data
}

export async function fetchAdminJobs(params?: { status?: string; page?: number; limit?: number }) {
  const { data } = await apiClient.get<AdminJobListResponse>(apiEndpoints.admin.jobs.list, {
    params,
  })
  return data
}

export async function createAdminJob(payload: AdminJobCreate) {
  const { data } = await apiClient.post(apiEndpoints.admin.jobs.list, payload)
  return data
}

export async function updateAdminJob(jobId: string, payload: AdminJobUpdate) {
  const { data } = await apiClient.patch(apiEndpoints.admin.jobs.detail(jobId), payload)
  return data
}

export async function archiveAdminJob(jobId: string) {
  await apiClient.post(apiEndpoints.admin.jobs.archive(jobId))
}

export async function fetchAdminJobSources() {
  const { data } = await apiClient.get<JobSourcePublic[]>(apiEndpoints.admin.jobs.sources)
  return data
}

export async function fetchAdminImportRuns() {
  const { data } = await apiClient.get<IngestionRunPublic[]>(apiEndpoints.admin.jobs.imports)
  return data
}

export async function fetchAdminImportErrors(runId: string) {
  const { data } = await apiClient.get<IngestionErrorPublic[]>(
    apiEndpoints.admin.jobs.importErrors(runId),
  )
  return data
}

export async function validateJobImport(file: File) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<ImportPreviewResponse>(
    apiEndpoints.admin.jobs.importValidate,
    form,
    { headers: { 'Content-Type': undefined } },
  )
  return data
}

export async function confirmJobImport(payload: ImportConfirmRequest) {
  const { data } = await apiClient.post<ImportConfirmResponse>(
    apiEndpoints.admin.jobs.importConfirm,
    payload,
  )
  return data
}
