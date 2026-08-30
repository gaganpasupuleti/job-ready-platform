import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export interface ContentCandidate {
  id: string
  batch_id: string
  content_hash: string
  validation_status: string
  review_status: string
  validation_errors: { errors?: string[]; warnings?: string[] } | null
  payload_json: Record<string, unknown>
  published_question_id: string | null
  created_at: string
}

export interface ContentBatch {
  id: string
  batch_date: string
  content_type: string
  target_role: string | null
  target_skill: string | null
  generated_count: number
  accepted_count: number
  rejected_count: number
  status: string
  source_filename: string | null
  created_at: string
  candidates?: ContentCandidate[]
}

export async function fetchContentBatches() {
  const { data } = await apiClient.get<{ items: ContentBatch[]; total: number }>(
    apiEndpoints.admin.contentBatches,
  )
  return data
}

export async function fetchContentBatch(id: string) {
  const { data } = await apiClient.get<ContentBatch>(apiEndpoints.admin.contentBatch(id))
  return data
}

export async function fetchContentCandidates(params?: Record<string, string>) {
  const { data } = await apiClient.get<{ items: ContentCandidate[]; total: number }>(
    apiEndpoints.admin.contentCandidates,
    { params },
  )
  return data
}

export async function approveContentCandidate(id: string) {
  const { data } = await apiClient.post<ContentCandidate>(apiEndpoints.admin.contentApprove(id))
  return data
}

export async function rejectContentCandidate(id: string) {
  const { data } = await apiClient.post<ContentCandidate>(apiEndpoints.admin.contentReject(id))
  return data
}

export async function bulkApproveContent(ids: string[]) {
  const { data } = await apiClient.post<{ approved: number; errors: string[] }>(
    apiEndpoints.admin.contentBulkApprove,
    { ids },
  )
  return data
}

export async function updateContentCandidate(id: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.patch<ContentCandidate>(
    apiEndpoints.admin.contentCandidate(id),
    payload,
  )
  return data
}

export async function fetchInterviewQuestions() {
  const { data } = await apiClient.get<{
    items: Array<{
      id: string
      slug: string
      question_text: string
      difficulty: string
      question_type: string
      experience_level: string
      skills: string[]
      roles: string[]
    }>
    total: number
  }>(apiEndpoints.interview.questions)
  return data
}

export async function fetchInterviewQuestion(slug: string) {
  const { data } = await apiClient.get<{
    slug: string
    question_text: string
    expected_answer: string
    explanation: string | null
    key_points: Array<{ point_text: string; sort_order: number }>
    skills: string[]
    roles: string[]
    difficulty: string
    experience_level: string
  }>(apiEndpoints.interview.question(slug))
  return data
}
