import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type { ReadinessOverview, RecommendationAction } from '@/types/readiness'

export async function fetchReadiness() {
  const { data } = await apiClient.get<ReadinessOverview>(apiEndpoints.readiness.overview)
  return data
}

export async function fetchSkillProfile() {
  const { data } = await apiClient.get(apiEndpoints.readiness.skills)
  return data
}

export async function fetchRoleComparison() {
  const { data } = await apiClient.get(apiEndpoints.readiness.roles)
  return data
}

export async function fetchRoleDetail(slug: string) {
  const { data } = await apiClient.get(apiEndpoints.readiness.roleDetail(slug))
  return data
}

export async function refreshReadiness() {
  const { data } = await apiClient.post<ReadinessOverview>(apiEndpoints.readiness.refresh)
  return data
}

export async function fetchRecommendations() {
  const { data } = await apiClient.get<RecommendationAction[]>(apiEndpoints.readiness.recommendations)
  return data
}
