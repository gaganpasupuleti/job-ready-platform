import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type { HealthResponse, ModulesResponse } from '@/types'

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>(apiEndpoints.health)
  return data
}

export async function fetchModules(): Promise<ModulesResponse> {
  const { data } = await apiClient.get<ModulesResponse>(apiEndpoints.modules)
  return data
}
