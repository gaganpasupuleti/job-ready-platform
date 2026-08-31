export type InterviewSessionMode = 'study' | 'mock' | 'rapid_review'
export type InterviewSessionSource = 'pack' | 'custom_filter' | 'retry_review'
export type InterviewSessionStatus = 'active' | 'completed' | 'abandoned'
export type InterviewSessionQuestionStatus = 'unseen' | 'viewed' | 'reviewed' | 'completed'
export type InterviewConfidence = 'low' | 'medium' | 'high'
export type InterviewSelfRating = 'needs_review' | 'partial' | 'good' | 'strong'
export type InterviewQuestionType =
  | 'technical'
  | 'hr'
  | 'behavioral'
  | 'scenario'
  | 'conceptual'
  | 'troubleshooting'
  | 'architecture'
  | 'situational'
export type ExperienceLevel = 'fresher' | 'junior' | 'intermediate' | 'senior'
export type Difficulty = 'easy' | 'medium' | 'hard'

export interface InterviewAnswerPoint {
  id: string
  point_text: string
  sort_order: number
}

export interface InterviewQuestionListItem {
  id: string
  slug: string
  question_text: string
  question_type: InterviewQuestionType | string
  difficulty: Difficulty | string
  experience_level: ExperienceLevel | string
  skills: string[]
  roles: string[]
}

export interface InterviewQuestionListResponse {
  items: InterviewQuestionListItem[]
  total: number
}

export interface InterviewQuestionDetail {
  id: string
  slug: string
  question_text: string
  question_type: InterviewQuestionType | string
  difficulty: Difficulty | string
  experience_level: ExperienceLevel | string
  expected_answer: string
  explanation: string | null
  key_points: InterviewAnswerPoint[]
  skills: string[]
  roles: string[]
  companies: string[]
}

export interface InterviewPack {
  id: string
  slug: string
  title: string
  description: string | null
  experience_level: ExperienceLevel | string | null
  question_count: number
}

export interface InterviewPackDetail extends InterviewPack {
  target_role: string | null
  target_company: string | null
  skills_covered: string[]
  difficulty_mix: Record<string, number>
  estimated_minutes: number | null
  active_session_id: string | null
}

export interface InterviewSessionSummary {
  id: string
  title: string
  mode: InterviewSessionMode
  source_type: InterviewSessionSource
  pack_id: string | null
  pack_slug: string | null
  question_count: number
  current_question_index: number
  status: InterviewSessionStatus
  started_at: string
  completed_at: string | null
  reviewed_count: number
  needs_review_count: number
  key_point_coverage_avg: number | null
}

export interface InterviewNavigatorItem {
  number: number
  status: InterviewSessionQuestionStatus
  needs_review: boolean
  current: boolean
}

export interface InterviewSessionQuestion {
  number: number
  question_id: string
  slug: string
  question_text: string
  question_type: InterviewQuestionType | string
  difficulty: Difficulty | string
  experience_level: ExperienceLevel | string
  skills: string[]
  roles: string[]
  companies: string[]
  status: InterviewSessionQuestionStatus
  answer_revealed: boolean
  expected_answer: string | null
  explanation: string | null
  key_points: InterviewAnswerPoint[]
  answer_text: string | null
  private_notes: string | null
  self_rating: InterviewSelfRating | null
  confidence_level: InterviewConfidence | null
  key_points_checked: string[]
  needs_review: boolean
  time_spent_seconds: number | null
  key_point_coverage: number | null
}

export interface InterviewSessionDetail {
  session: InterviewSessionSummary
  navigator: InterviewNavigatorItem[]
  current: InterviewSessionQuestion | null
}

export interface InterviewSessionCreatePayload {
  mode?: InterviewSessionMode
  source_type?: InterviewSessionSource
  pack_id?: string
  pack_slug?: string
  title?: string
  question_count?: number
  role?: string
  skill?: string
  company?: string
  difficulty?: Difficulty | string
  experience_level?: ExperienceLevel | string
  question_type?: InterviewQuestionType | string
  question_ids?: string[]
  deterministic?: boolean
}

export interface InterviewNotesPayload {
  answer_text?: string | null
  private_notes?: string | null
}

export interface InterviewReviewPayload {
  key_point_ids: string[]
  confidence: InterviewConfidence
  self_rating: InterviewSelfRating
  needs_review?: boolean | null
  time_spent_seconds?: number | null
}

export interface InterviewSkillBreakdown {
  skill: string
  question_count: number
  key_point_coverage_avg: number | null
}

export interface InterviewTypeBreakdown {
  question_type: string
  question_count: number
  needs_review_count: number
}

export interface InterviewSessionResults {
  session: InterviewSessionSummary
  questions_total: number
  reviewed_count: number
  needs_review_count: number
  strong: number
  good: number
  partial: number
  needs_review_rating: number
  key_point_coverage_avg: number | null
  confidence_breakdown: Record<string, number>
  skill_breakdown: InterviewSkillBreakdown[]
  type_breakdown: InterviewTypeBreakdown[]
  weak_question_ids: string[]
  label: string
}

export interface InterviewProgress {
  questions_reviewed: number
  sessions_completed: number
  needs_review: number
  high_confidence_percent: number | null
  average_key_point_coverage: number | null
  by_role: Record<string, number>
  by_skill: Record<string, number>
  by_type: Record<string, number>
  by_experience: Record<string, number>
}

export interface InterviewNeedsReviewItem {
  question_id: string
  slug: string
  question_text: string
  self_rating: InterviewSelfRating | null
  confidence_level: InterviewConfidence | null
  key_point_coverage: number | null
  needs_review: boolean
  skills: string[]
}

export interface InterviewHub {
  continue_session: InterviewSessionSummary | null
  packs: InterviewPack[]
  progress: InterviewProgress
  needs_review_count: number
  recent_sessions: InterviewSessionSummary[]
}

export interface CompanyPrepCard {
  slug: string
  name: string
  interview_pack_count: number
  practice_path_slugs: string[]
}

export interface CompanyPrepDetail {
  slug: string
  name: string
  disclaimer: string
  skills: string[]
  packs: InterviewPack[]
  practice_paths: Array<{ slug?: string; title?: string; href?: string; [key: string]: unknown }>
}

export interface AdminInterviewPackCreate {
  slug?: string | null
  title: string
  description?: string | null
  experience_level?: ExperienceLevel | string | null
  target_role?: string | null
  target_company?: string | null
  is_active?: boolean
  question_ids?: string[]
}

export interface AdminInterviewPackUpdate {
  title?: string | null
  description?: string | null
  experience_level?: ExperienceLevel | string | null
  target_role?: string | null
  target_company?: string | null
  is_active?: boolean | null
  question_ids?: string[] | null
}

export interface InterviewQuestionFilters {
  role?: string
  skill?: string
  difficulty?: string
  question_type?: string
  skip?: number
  limit?: number
}
