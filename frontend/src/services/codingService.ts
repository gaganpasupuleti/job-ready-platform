import { apiClient } from '@/api/client'

import { apiEndpoints } from '@/api/config'

import type {

  AdminCodingProblemDetail,

  CodingProblemDetail,

  CodingProblemListItem,

  CodingProgressSummary,

  ExecutionResponse,

  ExecutionStatusResponse,

  LanguageInfo,

  ProblemProgressStatus,

  SubmissionDetail,

  SubmissionListItem,

  SubmissionStatus,

} from '@/types/coding'



export interface CodingProblemsParams {
  search?: string
  difficulty?: string
  topic_slug?: string
  tag?: string
  status?: ProblemProgressStatus
  language_id?: number
  skip?: number
  limit?: number
}



export interface SubmissionsParams {

  problem_id?: string

  status?: SubmissionStatus

  language_id?: number

  difficulty?: string

  search?: string

  skip?: number

  limit?: number

}



function buildListParams(params?: Record<string, unknown>) {

  if (!params) return undefined

  const query: Record<string, string | number> = {}

  for (const [key, value] of Object.entries(params)) {

    if (value == null || value === '') continue

    if (key === 'supported_language_ids' && Array.isArray(value)) {

      query[key] = value.join(',')

    } else {

      query[key] = value as string | number

    }

  }

  return query

}



export async function fetchCodingProblems(params?: CodingProblemsParams) {

  const { data } = await apiClient.get<{ items: CodingProblemListItem[]; total: number }>(

    apiEndpoints.coding.problems,

    { params: buildListParams(params as Record<string, unknown>) },

  )

  return data

}



export async function fetchCodingProblem(problemId: string) {
  const { data } = await apiClient.get<CodingProblemDetail>(apiEndpoints.coding.problem(problemId))
  return data
}

export async function fetchCodingNavigation(problemId: string) {
  const { data } = await apiClient.get<{
    previous: { id: string; slug: string; title: string; status?: string | null; href: string } | null
    next: { id: string; slug: string; title: string; status?: string | null; href: string } | null
    position: number
    total: number
    items: Array<{ id: string; slug: string; title: string; status?: string | null; href: string }>
  }>(apiEndpoints.coding.navigation(problemId))
  return data
}



export async function runCode(problemId: string, sourceCode: string, languageId: number) {

  const { data } = await apiClient.post<ExecutionResponse>(apiEndpoints.coding.run(problemId), {

    source_code: sourceCode,

    language_id: languageId,

  })

  return data

}



export async function submitCode(problemId: string, sourceCode: string, languageId: number) {

  const { data } = await apiClient.post<ExecutionResponse>(apiEndpoints.coding.submit(problemId), {

    source_code: sourceCode,

    language_id: languageId,

  })

  return data

}



export async function fetchCodingProgress() {

  const { data } = await apiClient.get<CodingProgressSummary>(apiEndpoints.coding.progress)

  return data

}



export async function fetchSubmissions(params?: SubmissionsParams) {

  const { data } = await apiClient.get<{ items: SubmissionListItem[]; total: number }>(

    apiEndpoints.coding.submissions,

    { params: buildListParams(params as Record<string, unknown>) },

  )

  return data

}



export async function fetchSubmission(submissionId: string) {

  const { data } = await apiClient.get<SubmissionDetail>(

    apiEndpoints.coding.submission(submissionId),

  )

  return data

}



export async function fetchLanguages() {

  const { data } = await apiClient.get<LanguageInfo[]>(apiEndpoints.coding.languages)

  return data

}



export async function fetchExecutionStatus() {

  const { data } = await apiClient.get<ExecutionStatusResponse>(

    apiEndpoints.coding.executionStatus,

  )

  return data

}



export async function toggleCodingBookmark(problemId: string) {

  const { data } = await apiClient.post<{ bookmarked: boolean }>(

    apiEndpoints.coding.bookmark(problemId),

  )

  return data

}



export async function fetchCodingBookmarks() {
  const { data } = await apiClient.get<CodingProblemListItem[]>(apiEndpoints.coding.bookmarks)
  return { items: data, total: data.length }
}



export async function fetchAdminCodingProblems() {

  const { data } = await apiClient.get<{ items: CodingProblemListItem[]; total: number }>(

    apiEndpoints.admin.codingProblems,

  )

  return data

}



export async function fetchAdminCodingProblem(problemId: string) {

  const { data } = await apiClient.get<AdminCodingProblemDetail>(

    apiEndpoints.admin.codingProblem(problemId),

  )

  return data

}



export async function createAdminCodingProblem(payload: Record<string, unknown>) {

  const { data } = await apiClient.post<AdminCodingProblemDetail>(

    apiEndpoints.admin.codingProblems,

    payload,

  )

  return data

}



export async function updateAdminCodingProblem(problemId: string, payload: Record<string, unknown>) {

  const { data } = await apiClient.put<AdminCodingProblemDetail>(

    apiEndpoints.admin.codingProblem(problemId),

    payload,

  )

  return data

}



export async function deleteAdminCodingProblem(problemId: string) {

  await apiClient.delete(apiEndpoints.admin.codingProblem(problemId))

}

