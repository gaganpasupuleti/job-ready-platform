/** Pure view rules for Overview. This module does not fetch or invent metrics. */

const SOURCE_ID = /^[0-9a-f-]{36}$/i

export type RecentPracticeLink = {
  kind: string
  source_id: string
  status: string
}

export type QuizStatus = 'not_started' | 'in_progress' | 'completed'

export type QuizLink = {
  topic_slug: string
  topic_name: string
  category_name: string
  attempt_status: QuizStatus
}

export type SectionQuery = {
  data?: unknown
  isError: boolean
  fetchStatus: string
}

export function recentPracticeHref(item: RecentPracticeLink): string | null {
  if (!SOURCE_ID.test(item.source_id)) return null
  if (item.kind === 'mcq_session' && item.status === 'completed') {
    return `/practice/sessions/${item.source_id}/results`
  }
  if (item.kind === 'mcq_session' && (item.status === 'active' || item.status === 'abandoned')) {
    return `/practice/sessions/${item.source_id}`
  }
  if (item.kind === 'coding_submit') return `/submissions/${item.source_id}`
  if (item.kind === 'sql_submit') return `/sql/submissions/${item.source_id}`
  return null
}

export function practiceCatalogHref(categoryName: string): string {
  if (categoryName.trim().toLowerCase().includes('aptitude')) return '/practice/aptitude'
  return '/practice/mcq'
}

export function quizStatusCounts(quizzes: QuizLink[]) {
  return {
    not_started: quizzes.filter((quiz) => quiz.attempt_status === 'not_started').length,
    in_progress: quizzes.filter((quiz) => quiz.attempt_status === 'in_progress').length,
    completed: quizzes.filter((quiz) => quiz.attempt_status === 'completed').length,
  }
}

const QUIZ_ORDER: Record<QuizStatus, number> = {
  in_progress: 0,
  not_started: 1,
  completed: 2,
}

export function visibleQuizzes(quizzes: QuizLink[], limit = 6) {
  return [...quizzes].sort((left, right) => QUIZ_ORDER[left.attempt_status] - QUIZ_ORDER[right.attempt_status]).slice(0, limit)
}

export function mcqAccuracyState(percent: number | null | undefined): { kind: 'empty' } | { kind: 'value'; label: string } {
  if (typeof percent !== 'number' || Number.isNaN(percent)) return { kind: 'empty' }
  return { kind: 'value', label: `${percent}%` }
}

export function sectionUnavailable(query: SectionQuery) {
  return query.data == null && (query.isError || query.fetchStatus === 'paused')
}

export function sectionStaleMessage(query: SectionQuery, online: boolean) {
  if (query.data == null) return null
  if (!online && (query.isError || query.fetchStatus === 'paused')) {
    return 'Could not reach the server. Check your connection and retry.'
  }
  if (query.isError) return 'Could not refresh this section. The last loaded data is still shown.'
  return null
}
