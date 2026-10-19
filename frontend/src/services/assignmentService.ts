import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export interface AssignmentReport {
  id: string
  student_name: string
  student_email: string
  title: string
  link: string
  kind: string
  note: string | null
  question: string | null
  project_id: string | null
  project_title: string | null
  status: string
  review_note: string | null
  graded: boolean
  submitted_at: string | null
}

export interface AssignmentDraft {
  title: string
  link: string
  note?: string
  question?: string
  project_id?: string
}

export async function fetchMyAssignments() {
  const { data } = await apiClient.get<AssignmentReport[]>(apiEndpoints.assignments.list)
  return data
}

export async function submitManualAssignment(payload: AssignmentDraft) {
  const { data } = await apiClient.post<AssignmentReport>(apiEndpoints.assignments.list, payload)
  return data
}

export async function fetchAssignmentQueue() {
  const { data } = await apiClient.get<AssignmentReport[]>(apiEndpoints.admin.assignments)
  return data
}

export async function saveAssignmentReview(id: string, review_note: string) {
  const { data } = await apiClient.patch<AssignmentReport>(apiEndpoints.admin.assignment(id), {
    review_note,
  })
  return data
}
