import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type { MistakeItem, MistakeSummary } from '@/types/readiness'

export async function fetchMistakes(params?: { source_type?: string; view?: string }) {
  const { data } = await apiClient.get<MistakeItem[]>(apiEndpoints.mistakes.list, { params })
  return data
}

export async function fetchMistakeSummary() {
  const { data } = await apiClient.get<MistakeSummary>(apiEndpoints.mistakes.summary)
  return data
}

export async function markMistakeReviewed(id: string) {
  const { data } = await apiClient.post<MistakeItem>(apiEndpoints.mistakes.review(id))
  return data
}

export async function resolveMistake(id: string) {
  const { data } = await apiClient.patch<MistakeItem>(apiEndpoints.mistakes.detail(id))
  return data
}
