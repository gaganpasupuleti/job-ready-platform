import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type {
  AdminInterviewPackCreate,
  AdminInterviewPackUpdate,
  CompanyPrepCard,
  CompanyPrepDetail,
  InterviewHub,
  InterviewNeedsReviewItem,
  InterviewNotesPayload,
  InterviewPack,
  InterviewPackDetail,
  InterviewProgress,
  InterviewQuestionDetail,
  InterviewQuestionFilters,
  InterviewQuestionListResponse,
  InterviewReviewPayload,
  InterviewSessionCreatePayload,
  InterviewSessionDetail,
  InterviewSessionQuestion,
  InterviewSessionResults,
  InterviewSessionSummary,
} from '@/types/interview'

export async function fetchInterviewHub() {
  const { data } = await apiClient.get<InterviewHub>(apiEndpoints.interviews.hub)
  return data
}

export async function fetchInterviewQuestions(params?: InterviewQuestionFilters) {
  const { data } = await apiClient.get<InterviewQuestionListResponse>(
    apiEndpoints.interview.questions,
    { params },
  )
  return data
}

export async function fetchInterviewQuestion(slugOrId: string) {
  const { data } = await apiClient.get<InterviewQuestionDetail>(
    apiEndpoints.interview.question(slugOrId),
  )
  return data
}

export async function fetchInterviewPacks() {
  const { data } = await apiClient.get<InterviewPack[]>(apiEndpoints.interview.packs)
  return data
}

export async function fetchInterviewPackDetail(slug: string) {
  const { data } = await apiClient.get<InterviewPackDetail>(apiEndpoints.interviews.pack(slug))
  return data
}

export async function createInterviewSession(payload: InterviewSessionCreatePayload) {
  const { data } = await apiClient.post<InterviewSessionDetail>(
    apiEndpoints.interviews.sessions,
    payload,
  )
  return data
}

export async function fetchInterviewSession(sessionId: string) {
  const { data } = await apiClient.get<InterviewSessionDetail>(
    apiEndpoints.interviews.session(sessionId),
  )
  return data
}

export async function fetchInterviewSessionQuestion(sessionId: string, number: number) {
  const { data } = await apiClient.get<InterviewSessionQuestion>(
    apiEndpoints.interviews.question(sessionId, number),
  )
  return data
}

export async function saveInterviewNotes(
  sessionId: string,
  number: number,
  payload: InterviewNotesPayload,
) {
  const { data } = await apiClient.post<InterviewSessionQuestion>(
    apiEndpoints.interviews.notes(sessionId, number),
    payload,
  )
  return data
}

export async function revealInterviewAnswer(sessionId: string, number: number) {
  const { data } = await apiClient.post<InterviewSessionQuestion>(
    apiEndpoints.interviews.reveal(sessionId, number),
  )
  return data
}

export async function submitInterviewReview(
  sessionId: string,
  number: number,
  payload: InterviewReviewPayload,
) {
  const { data } = await apiClient.post<InterviewSessionQuestion>(
    apiEndpoints.interviews.review(sessionId, number),
    payload,
  )
  return data
}

export async function completeInterviewSession(sessionId: string) {
  const { data } = await apiClient.post<InterviewSessionResults>(
    apiEndpoints.interviews.complete(sessionId),
  )
  return data
}

export async function abandonInterviewSession(sessionId: string) {
  const { data } = await apiClient.post<InterviewSessionSummary>(
    apiEndpoints.interviews.abandon(sessionId),
  )
  return data
}

export async function fetchInterviewResults(sessionId: string) {
  const { data } = await apiClient.get<InterviewSessionResults>(
    apiEndpoints.interviews.results(sessionId),
  )
  return data
}

export async function fetchInterviewHistory(params?: { skip?: number; limit?: number }) {
  const { data } = await apiClient.get<InterviewSessionSummary[]>(apiEndpoints.interviews.history, {
    params,
  })
  return data
}

export async function fetchInterviewProgress() {
  const { data } = await apiClient.get<InterviewProgress>(apiEndpoints.interviews.progress)
  return data
}

export async function fetchInterviewReviewQueue() {
  const { data } = await apiClient.get<InterviewNeedsReviewItem[]>(
    apiEndpoints.interviews.reviewQueue,
  )
  return data
}

export async function markInterviewQuestionReviewed(questionId: string) {
  const { data } = await apiClient.post<InterviewNeedsReviewItem>(
    apiEndpoints.interviews.markReviewed(questionId),
  )
  return data
}

export async function fetchCompanyPrepList() {
  const { data } = await apiClient.get<CompanyPrepCard[]>(apiEndpoints.interviews.companyPrep)
  return data
}

export async function fetchCompanyPrepDetail(slug: string) {
  const { data } = await apiClient.get<CompanyPrepDetail>(
    apiEndpoints.interviews.companyPrepDetail(slug),
  )
  return data
}

export async function fetchAdminInterviewPacks() {
  const { data } = await apiClient.get<InterviewPack[]>(apiEndpoints.admin.interviewPacks)
  return data
}

export async function createAdminInterviewPack(payload: AdminInterviewPackCreate) {
  const { data } = await apiClient.post<InterviewPack>(apiEndpoints.admin.interviewPacks, payload)
  return data
}

export async function updateAdminInterviewPack(packId: string, payload: AdminInterviewPackUpdate) {
  const { data } = await apiClient.patch<InterviewPack>(
    apiEndpoints.admin.interviewPack(packId),
    payload,
  )
  return data
}
