import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export type PracticeTracker = {
  week: {
    timezone: 'UTC'
    start: string
    end: string
    boundary: string
  }
  weekly_activity: {
    mcq_finalized_answers: number
    coding_submits: number
    sql_submits: number
    total: number
  }
  mcq_accuracy: {
    graded_answers: number
    correct_answers: number
    accuracy_percent: number | null
  }
  completed_sessions: number
  in_progress_sessions: number
  recent_practice: Array<{
    kind: 'mcq_session' | 'coding_submit' | 'sql_submit'
    source_id: string
    title: string
    status: string
    occurred_at: string
  }>
  weak_topics: Array<{
    topic_id: string
    topic_name: string
    topic_slug: string
    category_name: string
    graded_answers: number
    correct_answers: number
    incorrect_answers: number
    accuracy_percent: number
  }>
  quizzes: Array<{
    topic_id: string
    topic_name: string
    topic_slug: string
    category_id: string
    category_name: string
    active_question_count: number
    attempt_status: 'not_started' | 'in_progress' | 'completed'
  }>
  recently_published: {
    available: boolean
    reason: string
  }
}

export async function fetchPracticeTracker() {
  const { data } = await apiClient.get<PracticeTracker>(apiEndpoints.practice.tracker)
  return data
}
