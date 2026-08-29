export type Difficulty = 'easy' | 'medium' | 'hard'
export type PracticeMode = 'practice' | 'exam'

export interface SubtopicBrief {
  id: string
  name: string
  slug: string
}

export interface TopicBrief {
  id: string
  name: string
  slug: string
  subtopics: SubtopicBrief[]
}

export interface CategoryBrief {
  id: string
  name: string
  slug: string
  topics: TopicBrief[]
}

export interface DomainBrief {
  id: string
  name: string
  slug: string
  categories: CategoryBrief[]
}

export interface CatalogResponse {
  domains: DomainBrief[]
}

export interface CreateSessionPayload {
  category_id?: string
  topic_id?: string
  difficulty?: Difficulty
  question_count: number
  mode: PracticeMode
}

export interface SessionSummary {
  id: string
  mode: PracticeMode
  status: string
  question_count: number
  score: number
  correct_count: number
  incorrect_count: number
  unanswered_count: number
  started_at: string
  completed_at?: string | null
}

export interface SessionDetail extends SessionSummary {
  category_id?: string | null
  topic_id?: string | null
  difficulty?: Difficulty | null
  answered_count: number
  expires_at?: string | null
  remaining_seconds?: number | null
  duration_minutes?: number | null
}

export interface SessionQuestionOverview {
  question_number: number
  answered: boolean
  marked_for_review: boolean
}

export interface SessionOverviewResponse {
  questions: SessionQuestionOverview[]
}

export interface PracticeBookmarkItem {
  id: string
  title?: string | null
  question_text: string
  difficulty: Difficulty
  topic_name?: string | null
  bookmarked_at?: string
}

export interface QuestionOptionPublic {
  id: string
  option_text: string
  sort_order: number
}

export interface QuestionPublic {
  id: string
  question_type: string
  title: string | null
  question_text: string
  difficulty: Difficulty
  marks: number
  negative_marks: number
  estimated_time_seconds: number
  options: QuestionOptionPublic[]
  topic_name?: string | null
  skills: string[]
}

export interface SessionQuestionResponse {
  question_number: number
  total_questions: number
  question: QuestionPublic
  answered: boolean
  bookmarked: boolean
  marked_for_review?: boolean
  selected_option_ids?: string[]
}

export interface AnswerFeedback {
  is_correct: boolean
  marks_awarded: number
  correct_option_ids: string[]
  selected_option_ids: string[]
  explanation?: string | null
  options: Array<{ id: string; option_text: string; is_correct: boolean }>
  topic_name?: string | null
  difficulty?: Difficulty | null
  skills: string[]
  reveal_feedback: boolean
}

export interface AnswerResponse {
  question_number: number
  answered: boolean
  feedback?: AnswerFeedback | null
}

export interface TopicPerformance {
  topic_name: string
  accuracy: number
  total: number
  correct: number
}

export interface QuestionReviewItem {
  question_number: number
  question_text: string
  selected_option_ids: string[]
  correct_option_ids: string[]
  selected_option_texts: string[]
  correct_option_texts: string[]
  explanation?: string | null
  is_correct: boolean
  marks_awarded: number
}

export interface SessionResultsResponse {
  session: SessionSummary
  accuracy: number
  time_taken_seconds: number
  topic_performance: TopicPerformance[]
  questions: QuestionReviewItem[]
}

export interface HistoryItem {
  id: string
  mode: PracticeMode
  status: string
  question_count: number
  score: number
  correct_count: number
  incorrect_count: number
  started_at: string
  completed_at?: string | null
  category_name?: string | null
  topic_name?: string | null
}

export interface HistoryResponse {
  sessions: HistoryItem[]
}
