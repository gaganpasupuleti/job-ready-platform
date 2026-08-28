import { apiClient, setAuthToken } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type { AuthResponse, LoginPayload, RegisterPayload, User } from '@/types/auth'

export async function register(payload: RegisterPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>(apiEndpoints.auth.register, payload)
  setAuthToken(data.access_token)
  return data
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>(apiEndpoints.auth.login, payload)
  setAuthToken(data.access_token)
  return data
}

export async function fetchMe(): Promise<User> {
  const { data } = await apiClient.get<User>(apiEndpoints.auth.me)
  return data
}

export async function logoutApi(): Promise<void> {
  try {
    await apiClient.post(apiEndpoints.auth.logout)
  } finally {
    setAuthToken(null)
  }
}
