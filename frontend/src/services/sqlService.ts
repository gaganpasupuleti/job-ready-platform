import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type {
  AdminSqlProblemDetail,
  AdminSqlValidateResponse,
  SqlExecutionStatus,
  SqlProblemDetail,
  SqlProblemListItem,
  SqlProgressStatus,
  SqlProgressSummary,
  SqlRunResponse,
  SqlSolutionResponse,
  SqlSubmissionDetail,
  SqlSubmissionListItem,
  SqlSubmissionStatus,
  SqlSubmitResponse,
  SqlTablePreview,
  SqlTableSchemaPublic,
} from '@/types/sql'

export interface SqlProblemsParams {
  search?: string
  difficulty?: string
  topic_slug?: string
  tag?: string
  status?: SqlProgressStatus
  skip?: number
  limit?: number
}

export interface SqlSubmissionsParams {
  problem_id?: string
  status?: SqlSubmissionStatus
  skip?: number
  limit?: number
}

function buildListParams(params?: Record<string, unknown>) {
  if (!params) return undefined
  const query: Record<string, string | number> = {}
  for (const [key, value] of Object.entries(params)) {
    if (value == null || value === '') continue
    query[key] = value as string | number
  }
  return query
}

export async function fetchSqlProblems(params?: SqlProblemsParams) {
  const { data } = await apiClient.get<{ items: SqlProblemListItem[]; total: number }>(
    apiEndpoints.sql.problems,
    { params: buildListParams(params as Record<string, unknown>) },
  )
  return data
}

export async function fetchSqlProblem(slugOrId: string) {
  const { data } = await apiClient.get<SqlProblemDetail>(apiEndpoints.sql.problem(slugOrId))
  return data
}

export async function fetchSqlSchema(problemId: string) {
  const { data } = await apiClient.get<SqlTableSchemaPublic[]>(apiEndpoints.sql.schema(problemId))
  return data
}

export async function fetchSqlTablePreview(problemId: string, tableName: string, limit = 10) {
  const { data } = await apiClient.get<SqlTablePreview>(
    apiEndpoints.sql.tablePreview(problemId, tableName),
    { params: { limit } },
  )
  return data
}

export async function runSqlQuery(problemId: string, query: string) {
  const { data } = await apiClient.post<SqlRunResponse>(apiEndpoints.sql.run(problemId), { query })
  return data
}

export async function submitSqlQuery(problemId: string, query: string) {
  const { data } = await apiClient.post<SqlSubmitResponse>(apiEndpoints.sql.submit(problemId), {
    query,
  })
  return data
}

export async function fetchSqlProgress() {
  const { data } = await apiClient.get<SqlProgressSummary>(apiEndpoints.sql.progress)
  return data
}

export async function fetchSqlSubmissions(params?: SqlSubmissionsParams) {
  const { data } = await apiClient.get<{ items: SqlSubmissionListItem[]; total: number }>(
    apiEndpoints.sql.submissions,
    { params: buildListParams(params as Record<string, unknown>) },
  )
  return data
}

export async function fetchSqlSubmission(submissionId: string) {
  const { data } = await apiClient.get<SqlSubmissionDetail>(
    apiEndpoints.sql.submission(submissionId),
  )
  return data
}

export async function fetchSqlProblemSubmissions(problemId: string, limit = 20) {
  const { data } = await apiClient.get<{ items: SqlSubmissionListItem[]; total: number }>(
    apiEndpoints.sql.problemSubmissions(problemId),
    { params: { limit } },
  )
  return data
}

export async function fetchSqlExecutionStatus() {
  const { data } = await apiClient.get<SqlExecutionStatus>(apiEndpoints.sql.executionStatus)
  return data
}

export async function toggleSqlBookmark(problemId: string) {
  const { data } = await apiClient.post<{ bookmarked: boolean }>(
    apiEndpoints.sql.bookmark(problemId),
  )
  return data
}

export async function fetchSqlBookmarks() {
  const { data } = await apiClient.get<SqlProblemListItem[]>(apiEndpoints.sql.bookmarks)
  return { items: data, total: data.length }
}

export async function fetchSqlSolution(problemId: string) {
  const { data } = await apiClient.get<SqlSolutionResponse>(apiEndpoints.sql.solution(problemId))
  return data
}

export async function fetchAdminSqlProblems() {
  const { data } = await apiClient.get<{ items: SqlProblemListItem[]; total: number }>(
    apiEndpoints.admin.sqlProblems,
  )
  return data
}

export async function fetchAdminSqlProblem(problemId: string) {
  const { data } = await apiClient.get<AdminSqlProblemDetail>(
    apiEndpoints.admin.sqlProblem(problemId),
  )
  return data
}

export async function createAdminSqlProblem(payload: Record<string, unknown>) {
  const { data } = await apiClient.post<AdminSqlProblemDetail>(
    apiEndpoints.admin.sqlProblems,
    payload,
  )
  return data
}

export async function updateAdminSqlProblem(problemId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.put<AdminSqlProblemDetail>(
    apiEndpoints.admin.sqlProblem(problemId),
    payload,
  )
  return data
}

export async function deleteAdminSqlProblem(problemId: string) {
  await apiClient.delete(apiEndpoints.admin.sqlProblem(problemId))
}

export async function validateAdminSqlProblem(problemId: string) {
  const { data } = await apiClient.post<AdminSqlValidateResponse>(
    apiEndpoints.admin.sqlValidate(problemId),
  )
  return data
}
