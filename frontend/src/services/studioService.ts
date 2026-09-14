import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export type StudioCatalog = {
  families: { id: string; label: string; count: number }[]
  skills: { id: string; count: number }[]
  levels: { id: string; count: number }[]
  kinds: { id: string; count: number }[]
  materials: {
    key: string
    title: string
    kind: string
    level: string
    minutes: number
    families: string[]
    skills: string[]
    read: boolean
    updated_at: string | null
  }[]
  assignments: {
    key: string
    title: string
    mode: string
    families: string[]
    in_progress: boolean
    unavailable?: boolean
    requires_runtime?: string | null
  }[]
  packs: { key: string; title: string; kind: string; questions: number; families: string[] }[]
}

export type MaterialDetail = {
  key: string
  title: string
  summary: string
  kind: string
  level: string
  audience: string | null
  minutes: number
  objectives: string[]
  prerequisites: string[]
  body_md: string
  examples: string[]
  exercises: string[]
  summary_md: string
  sources: { label: string; url: string }[]
  families: string[]
  skills: string[]
  version: number
  updated_at: string | null
  has_download: boolean
  read: boolean
  related_pack: string | null
}

export type AssignmentDetail = {
  key: string
  title: string
  goal: string
  brief_md: string
  requirements: string[]
  deliverables: string[]
  hints: string[]
  prerequisites: string[]
  rubric: { criterion: string; points: number }[]
  mode: string
  minutes: number
  due_at: string | null
  families: string[]
  version: number
  sql_problem_slug: string | null
  local_python: boolean
  requires_runtime?: string | null
  unavailable?: boolean
  unavailable_reason?: string | null
  submissions: {
    id: string
    attempt: number
    status: string
    version: number
    answer_text: string
    evidence_url: string | null
    brief: string | null
    rubric: { criterion: string; points: number }[] | null
    submitted_at: string | null
    reviews: { feedback: string; grade: string | null; version: number; reviewed_at?: string }[]
  }[]
}

export async function fetchStudioCatalog(params: Record<string, string>) {
  const { data } = await apiClient.get<StudioCatalog>(apiEndpoints.learn.studioCatalog, { params })
  return data
}

export async function fetchMaterial(key: string) {
  const { data } = await apiClient.get<MaterialDetail>(apiEndpoints.learn.studioMaterial(key))
  return data
}

export async function markMaterialRead(key: string) {
  const { data } = await apiClient.post(apiEndpoints.learn.studioMaterialRead(key))
  return data
}

export function materialDownloadUrl(key: string) {
  return apiEndpoints.learn.studioMaterialDownload(key)
}

export async function fetchAssignment(key: string) {
  const { data } = await apiClient.get<AssignmentDetail>(apiEndpoints.learn.studioAssignment(key))
  return data
}

export async function saveAssignmentDraft(key: string, payload: { answer_text: string; evidence_url: string }) {
  const { data } = await apiClient.post(apiEndpoints.learn.studioAssignmentDraft(key), payload)
  return data
}

export async function submitAssignment(key: string, payload: { answer_text: string; evidence_url: string }) {
  const { data } = await apiClient.post(apiEndpoints.learn.studioAssignmentSubmit(key), payload)
  return data
}

export async function startPack(key: string) {
  const { data } = await apiClient.post<{ session_id: string }>(apiEndpoints.learn.studioPackStart(key))
  return data
}

export async function fetchReviewQueue() {
  const { data } = await apiClient.get<
    { id: string; status: string; version: number; assignment_key: string | null; title: string | null; answer_text: string; evidence_url: string | null; brief: string | null; rubric: { criterion: string; points: number }[] | null }[]
  >(apiEndpoints.learn.studioReviews)
  return data
}

export async function reviewSubmission(id: string, payload: { feedback: string; grade: string | null }) {
  const { data } = await apiClient.post(apiEndpoints.learn.studioReview(id), payload)
  return data
}

export type SyllabusTracks = {
  tracks: {
    id: string
    title: string
    units: {
      id: string
      title: string
      position: number
      lessons: {
        key: string
        title: string
        position: number
        status: string
        minutes: number | null
        material_key: string | null
        href: string | null
      }[]
    }[]
  }[]
}

export type SyllabusLesson = {
  key: string
  title: string
  track: string
  track_title: string
  unit: string
  unit_title: string
  position: number
  status: string
  minutes: number | null
  prerequisites: string[]
  material_key: string | null
  video: { url: string; channel: string; topic: string; verified_on: string } | null
  syllabus_position: number
  syllabus_total: number
  previous: { key: string; title: string; status: string; material_key: string | null; href: string } | null
  next: { key: string; title: string; status: string; material_key: string | null; href: string } | null
  material: MaterialDetail | null
  practice: { key: string; stem: string; options: { key: string; text: string }[] }[]
}

export async function fetchSyllabusTracks() {
  const { data } = await apiClient.get<SyllabusTracks>(apiEndpoints.learn.studioSyllabus)
  return data
}

export async function fetchSyllabusLesson(key: string) {
  const { data } = await apiClient.get<SyllabusLesson>(apiEndpoints.learn.studioSyllabusLesson(key))
  return data
}

export async function checkSyllabusPractice(key: string, questionKey: string, selected: string[]) {
  const { data } = await apiClient.post<{
    correct: boolean
    selected: string[]
    correct_keys: string[]
    explanation: string
    options: { key: string; text: string; correct: boolean }[]
    competence: boolean
    note: string
  }>(apiEndpoints.learn.studioSyllabusPractice(key, questionKey), { selected })
  return data
}
