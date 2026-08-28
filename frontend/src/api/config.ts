const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export const apiConfig = {
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
} as const

export const apiEndpoints = {
  health: '/api/v1/health',
  modules: '/api/v1/modules',
  auth: {
    register: '/api/v1/auth/register',
    login: '/api/v1/auth/login',
    me: '/api/v1/auth/me',
    logout: '/api/v1/auth/logout',
  },
  practice: {
    catalog: '/api/v1/practice/catalog',
    sessions: '/api/v1/practice/sessions',
    history: '/api/v1/practice/history',
    bookmark: (questionId: string) => `/api/v1/practice/questions/${questionId}/bookmark`,
    session: (sessionId: string) => `/api/v1/practice/sessions/${sessionId}`,
    question: (sessionId: string, number: number) =>
      `/api/v1/practice/sessions/${sessionId}/questions/${number}`,
    answer: (sessionId: string, number: number) =>
      `/api/v1/practice/sessions/${sessionId}/questions/${number}/answer`,
    complete: (sessionId: string) => `/api/v1/practice/sessions/${sessionId}/complete`,
    results: (sessionId: string) => `/api/v1/practice/sessions/${sessionId}/results`,
  },
  admin: {
    questions: '/api/v1/admin/questions',
    question: (id: string) => `/api/v1/admin/questions/${id}`,
    taxonomy: '/api/v1/admin/taxonomy',
  },
} as const

export const AUTH_TOKEN_KEY = 'jrp_access_token'
