import axios from 'axios'

import { apiConfig, AUTH_TOKEN_KEY } from '@/api/config'
import { clearAuthQueryCache } from '@/queryClient'

function bearerToken(headers: { get?: (name: string) => unknown; Authorization?: unknown } | undefined): string {
  if (!headers) return ''
  const raw = typeof headers.get === 'function' ? headers.get('Authorization') : headers.Authorization
  if (typeof raw !== 'string') return ''
  return raw.replace(/^Bearer\s+/i, '')
}

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
  (response) => {
    const sent = bearerToken(response.config.headers)
    const current = localStorage.getItem(AUTH_TOKEN_KEY) ?? ''
    if (sent && sent !== current) {
      return Promise.reject(new Error('Session changed'))
    }
    return response
  },
  (error) => {
    const status = error.response?.status
    const requestUrl = String(error.config?.url ?? '')
    const isAuthEndpoint = /\/auth\/(login|register)\b/.test(requestUrl)
    const sent = bearerToken(error.config?.headers)
    const current = localStorage.getItem(AUTH_TOKEN_KEY) ?? ''

    if (status === 401 && !isAuthEndpoint && (!sent || sent === current)) {
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
