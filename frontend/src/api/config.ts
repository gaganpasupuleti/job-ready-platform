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
    bookmarks: '/api/v1/practice/bookmarks',
    bookmark: (questionId: string) => `/api/v1/practice/questions/${questionId}/bookmark`,
    session: (sessionId: string) => `/api/v1/practice/sessions/${sessionId}`,
    navigator: (sessionId: string) => `/api/v1/practice/sessions/${sessionId}/navigator`,
    question: (sessionId: string, number: number) =>
      `/api/v1/practice/sessions/${sessionId}/questions/${number}`,
    answer: (sessionId: string, number: number) =>
      `/api/v1/practice/sessions/${sessionId}/questions/${number}/answer`,
    autosave: (sessionId: string, number: number) =>
      `/api/v1/practice/sessions/${sessionId}/questions/${number}/autosave`,
    complete: (sessionId: string) => `/api/v1/practice/sessions/${sessionId}/complete`,
    results: (sessionId: string) => `/api/v1/practice/sessions/${sessionId}/results`,
  },
  admin: {
    questions: '/api/v1/admin/questions',
    question: (id: string) => `/api/v1/admin/questions/${id}`,
    taxonomy: '/api/v1/admin/taxonomy',
    codingProblems: '/api/v1/admin/coding/problems',
    codingProblem: (id: string) => `/api/v1/admin/coding/problems/${id}`,
    codingTestCase: (id: string) => `/api/v1/admin/coding/test-cases/${id}`,
    codingProblemTestCases: (problemId: string) =>
      `/api/v1/admin/coding/problems/${problemId}/test-cases`,
    sqlProblems: '/api/v1/admin/sql/problems',
    sqlProblem: (id: string) => `/api/v1/admin/sql/problems/${id}`,
    sqlValidate: (id: string) => `/api/v1/admin/sql/problems/${id}/validate`,
  },
  coding: {
    problems: '/api/v1/coding/problems',
    problem: (id: string) => `/api/v1/coding/problems/${id}`,
    run: (id: string) => `/api/v1/coding/problems/${id}/run`,
    submit: (id: string) => `/api/v1/coding/problems/${id}/submit`,
    bookmark: (id: string) => `/api/v1/coding/problems/${id}/bookmark`,
    submissions: '/api/v1/coding/submissions',
    submission: (id: string) => `/api/v1/coding/submissions/${id}`,
    progress: '/api/v1/coding/progress',
    languages: '/api/v1/coding/languages',
    executionStatus: '/api/v1/coding/execution-status',
    bookmarks: '/api/v1/coding/bookmarks',
  },
  sql: {
    problems: '/api/v1/sql/problems',
    problem: (id: string) => `/api/v1/sql/problems/${id}`,
    schema: (id: string) => `/api/v1/sql/problems/${id}/schema`,
    tablePreview: (id: string, name: string) =>
      `/api/v1/sql/problems/${id}/tables/${encodeURIComponent(name)}/preview`,
    run: (id: string) => `/api/v1/sql/problems/${id}/run`,
    submit: (id: string) => `/api/v1/sql/problems/${id}/submit`,
    submissions: '/api/v1/sql/submissions',
    submission: (id: string) => `/api/v1/sql/submissions/${id}`,
    problemSubmissions: (id: string) => `/api/v1/sql/problems/${id}/submissions`,
    progress: '/api/v1/sql/progress',
    bookmark: (id: string) => `/api/v1/sql/problems/${id}/bookmark`,
    bookmarks: '/api/v1/sql/bookmarks',
    solution: (id: string) => `/api/v1/sql/problems/${id}/solution`,
    executionStatus: '/api/v1/sql/execution-status',
  },
} as const

export const AUTH_TOKEN_KEY = 'jrp_access_token'
