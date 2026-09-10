import axios from 'axios'

import { apiConfig, AUTH_TOKEN_KEY } from '@/api/config'
import { clearAuthQueryCache } from '@/queryClient'

export const apiClient = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: apiConfig.timeout,
  headers: apiConfig.headers,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const requestUrl = String(error.config?.url ?? '')
    const isAuthEndpoint = /\/auth\/(login|register)\b/.test(requestUrl)

    if (status === 401 && !isAuthEndpoint) {
      const currentToken = localStorage.getItem(AUTH_TOKEN_KEY)
      const rawAuth = error.config?.headers?.Authorization ?? error.config?.headers?.authorization
      const requestAuth = String(
        typeof rawAuth === 'string'
          ? rawAuth
          : rawAuth && typeof rawAuth === 'object' && 'toString' in rawAuth
            ? String(rawAuth)
            : '',
      )
      const currentBearer = currentToken ? `Bearer ${currentToken}` : ''
      // Ignore stale 401s from a previous account after a client-side switch.
      const matchesCurrentSession =
        Boolean(currentBearer) && requestAuth === currentBearer

      if (matchesCurrentSession) {
        localStorage.removeItem(AUTH_TOKEN_KEY)
        clearAuthQueryCache()
        if (typeof window !== 'undefined') {
          const path = window.location.pathname
          if (!path.startsWith('/login') && !path.startsWith('/register')) {
            const from = encodeURIComponent(path + window.location.search)
            window.location.assign(`/login?from=${from}`)
          }
        }
      }
    }

    const message =
      error.response?.data?.detail ?? error.message ?? 'An unexpected error occurred'
    return Promise.reject(new Error(typeof message === 'string' ? message : 'Request failed'))
  },
)

export function setAuthToken(token: string | null) {
  if (token) localStorage.setItem(AUTH_TOKEN_KEY, token)
  else localStorage.removeItem(AUTH_TOKEN_KEY)
}

export function getAuthToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY)
}

// Detached calls for AUTH e2e: in-flight requests survive queryClient.clear().
if (typeof window !== 'undefined' && import.meta.env.MODE !== 'production') {
  ;(window as unknown as { __jobReadyApiClient?: typeof apiClient }).__jobReadyApiClient =
    apiClient
}
