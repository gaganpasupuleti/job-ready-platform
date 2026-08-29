import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type {
  AnswerResponse,
  CatalogResponse,
  CreateSessionPayload,
  HistoryResponse,
  PracticeBookmarkItem,
  SessionDetail,
  SessionOverviewResponse,
  SessionQuestionResponse,
  SessionResultsResponse,
} from '@/types/practice'

export async function fetchCatalog(): Promise<CatalogResponse> {
  const { data } = await apiClient.get<CatalogResponse>(apiEndpoints.practice.catalog)
  return data
}

export async function createSession(payload: CreateSessionPayload): Promise<SessionDetail> {
  const { data } = await apiClient.post<SessionDetail>(apiEndpoints.practice.sessions, payload)
  return data
}

export async function fetchSession(sessionId: string): Promise<SessionDetail> {
  const { data } = await apiClient.get<SessionDetail>(apiEndpoints.practice.session(sessionId))
  return data
}

export async function fetchSessionQuestion(
  sessionId: string,
  questionNumber: number,
): Promise<SessionQuestionResponse> {
  const { data } = await apiClient.get<SessionQuestionResponse>(
    apiEndpoints.practice.question(sessionId, questionNumber),
  )
  return data
}

export async function submitAnswer(
  sessionId: string,
  questionNumber: number,
  selectedOptionIds: string[],
  timeSpentSeconds: number,
): Promise<AnswerResponse> {
  const { data } = await apiClient.post<AnswerResponse>(
    apiEndpoints.practice.answer(sessionId, questionNumber),
    { selected_option_ids: selectedOptionIds, time_spent_seconds: timeSpentSeconds },
  )
  return data
}

export async function completeSession(sessionId: string): Promise<SessionResultsResponse> {
  const { data } = await apiClient.post<SessionResultsResponse>(
    apiEndpoints.practice.complete(sessionId),
  )
  return data
}

export async function fetchResults(sessionId: string): Promise<SessionResultsResponse> {
  const { data } = await apiClient.get<SessionResultsResponse>(
    apiEndpoints.practice.results(sessionId),
  )
  return data
}

export async function fetchHistory(): Promise<HistoryResponse> {
  const { data } = await apiClient.get<HistoryResponse>(apiEndpoints.practice.history)
  return data
}

export async function toggleBookmark(questionId: string): Promise<{ bookmarked: boolean }> {
  const { data } = await apiClient.post<{ bookmarked: boolean }>(
    apiEndpoints.practice.bookmark(questionId),
  )
  return data
}

export async function fetchPracticeBookmarks(): Promise<PracticeBookmarkItem[]> {
  const { data } = await apiClient.get<PracticeBookmarkItem[]>(apiEndpoints.practice.bookmarks)
  return data
}

export async function fetchSessionOverview(sessionId: string): Promise<SessionOverviewResponse> {
  const { data } = await apiClient.get<{ items: SessionOverviewResponse['questions'] }>(
    apiEndpoints.practice.navigator(sessionId),
  )
  return { questions: data.items }
}

export async function autosaveAnswer(
  sessionId: string,
  questionNumber: number,
  selectedOptionIds: string[],
  markedForReview: boolean,
  timeSpentSeconds: number,
): Promise<{ saved: boolean }> {
  const { data } = await apiClient.post<{ saved: boolean }>(
    apiEndpoints.practice.autosave(sessionId, questionNumber),
    {
      selected_option_ids: selectedOptionIds,
      marked_for_review: markedForReview,
      time_spent_seconds: timeSpentSeconds,
    },
  )
  return data
}
