import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export interface PromptChallengeCard {
  id: string
  slug: string
  title: string
  description: string
  difficulty: string
  task_type: string
  mastery_threshold: number
  best_score: number
  status: string | null
  bookmarked: boolean
}

export interface PromptCasePublic {
  id: string
  input_text: string | null
  variables: Record<string, string>
  is_hidden: boolean
  weight: number
  sort_order: number
}

export interface PromptChallengeDetail {
  id: string
  slug: string
  title: string
  description: string
  difficulty: string
  task_type: string
  scenario: string
  instructions: string
  input_description: string
  expected_behavior: string
  starter_prompt: string | null
  max_prompt_length: number
  mastery_threshold: number
  evaluation_criteria_summary: string
  hints: string[]
  common_mistakes: string[]
  public_cases: PromptCasePublic[]
  hidden_case_count: number
  bookmarked: boolean
  best_score: number
  status: string | null
}

export interface PromptEvaluateResponse {
  overall_score: number
  passed_cases: number
  total_cases: number
  rubric_breakdown: Record<string, number>
  feedback: string
  case_results: Array<{
    case_id: string
    passed: boolean
    score: number
    feedback: string
    revealed: boolean
    check_results: Array<{ type?: string; passed: boolean; message: string }>
  }>
  mastered: boolean
  submission_id: string | null
  is_test: boolean
}

export interface PromptSubmissionListItem {
  id: string
  challenge_id: string
  challenge_title: string
  difficulty: string
  overall_score: number
  passed_cases: number
  total_cases: number
  is_test: boolean
  created_at: string
}

export interface PromptSubmissionDetail extends PromptEvaluateResponse {
  id: string
  challenge_title: string
  difficulty: string
  prompt_text: string
  created_at: string
}

export interface PromptBookmarkItem {
  id: string
  slug: string
  title: string
  difficulty: string
  task_type: string
}

export interface AIHomeResponse {
  tracks: Array<{ key: string; label: string; href: string }>
  continue_ai: string | null
  weak_topics: string[]
  prompt_progress: { attempted: number; mastered: number }
  topics: Array<{
    key: string
    label: string
    mcq_attempts: number
    mcq_accuracy: number | null
    prompt_attempts: number
    prompt_mastered: number
    best_prompt_score: number
  }>
  recommended: string[]
  paths: Array<{ slug: string; title: string; href: string }>
}

export async function fetchAiHome() {
  const { data } = await apiClient.get<AIHomeResponse>(apiEndpoints.ai.home)
  return data
}

export async function fetchAiProgress() {
  const { data } = await apiClient.get(apiEndpoints.ai.progress)
  return data as AIHomeResponse & { topics: AIHomeResponse['topics']; weak_topics: string[] }
}

export async function fetchPromptChallenges(difficulty?: string) {
  const { data } = await apiClient.get<PromptChallengeCard[]>(apiEndpoints.ai.prompts, {
    params: difficulty ? { difficulty } : undefined,
  })
  return data
}

export async function fetchPromptChallenge(slug: string) {
  const { data } = await apiClient.get<PromptChallengeDetail>(apiEndpoints.ai.prompt(slug))
  return data
}

export async function testPrompt(slug: string, prompt_text: string) {
  const { data } = await apiClient.post<PromptEvaluateResponse>(apiEndpoints.ai.test(slug), {
    prompt_text,
  })
  return data
}

export async function submitPrompt(slug: string, prompt_text: string) {
  const { data } = await apiClient.post<PromptEvaluateResponse>(apiEndpoints.ai.submit(slug), {
    prompt_text,
  })
  return data
}

export async function fetchPromptSubmissions() {
  const { data } = await apiClient.get<PromptSubmissionListItem[]>(apiEndpoints.ai.submissions)
  return data
}

export async function fetchPromptSubmission(id: string) {
  const { data } = await apiClient.get<PromptSubmissionDetail>(apiEndpoints.ai.submission(id))
  return data
}

export async function togglePromptBookmark(id: string) {
  const { data } = await apiClient.post<{ bookmarked: boolean }>(apiEndpoints.ai.bookmark(id))
  return data
}

export async function fetchPromptBookmarks() {
  const { data } = await apiClient.get<PromptBookmarkItem[]>(apiEndpoints.ai.bookmarks)
  return data
}

export async function fetchAdminAiCoverage() {
  const { data } = await apiClient.get(apiEndpoints.admin.aiHome)
  return data as Record<string, unknown>
}

export async function fetchAdminPrompts() {
  const { data } = await apiClient.get<Array<Record<string, unknown>>>(apiEndpoints.admin.aiPrompts)
  return data
}

export async function fetchAdminPrompt(id: string) {
  const { data } = await apiClient.get<Record<string, unknown>>(apiEndpoints.admin.aiPrompt(id))
  return data
}

export async function createAdminPrompt(payload: Record<string, unknown>) {
  const { data } = await apiClient.post(apiEndpoints.admin.aiPrompts, payload)
  return data
}

export async function updateAdminPrompt(id: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.patch(apiEndpoints.admin.aiPrompt(id), payload)
  return data
}

export async function validateAdminPrompt(id: string) {
  const { data } = await apiClient.post<{ ok: boolean; errors: string[] }>(
    apiEndpoints.admin.aiPromptValidate(id),
  )
  return data
}
