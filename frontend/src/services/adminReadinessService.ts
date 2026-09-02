import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export interface AdminRoleSkillRequirement {
  id: string
  skill_id: string
  skill_name: string
  importance: string
  weight: number
  minimum_readiness: number | null
  source: string
}

export interface AdminRoleReadiness {
  role: { id: string; name: string; slug: string }
  requirements: AdminRoleSkillRequirement[]
}

export async function fetchAdminReadinessRoles() {
  const { data } = await apiClient.get<AdminRoleReadiness[]>(apiEndpoints.admin.readiness.roles)
  return data
}

export async function upsertAdminRoleRequirement(
  roleId: string,
  skillId: string,
  payload: { skill_id: string; importance: string; weight: number; minimum_readiness?: number | null },
) {
  const { data } = await apiClient.put(
    `${apiEndpoints.admin.readiness.roles}/${roleId}/requirements/${skillId}`,
    payload,
  )
  return data
}

export async function deleteAdminRoleRequirement(roleId: string, skillId: string) {
  await apiClient.delete(`${apiEndpoints.admin.readiness.roles}/${roleId}/requirements/${skillId}`)
}
