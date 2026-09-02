export interface ReadinessOverview {
  target_role: { id: string; name: string; slug: string } | null
  score: number | null
  has_minimum_evidence: boolean
  evidence_strength: string
  core_coverage: { covered: number; total: number }
  skills: SkillReadinessItem[]
  strong_skills: string[]
  developing_skills: string[]
  missing_skills: string[]
  why_breakdown: WhyBreakdownItem[]
  trend: { score: number; created_at: string; evidence_strength: string }[]
  recommended_actions: RecommendationAction[]
  message: string | null
}

export interface SkillReadinessItem {
  skill_id?: string
  skill_name?: string
  skill_slug?: string
  importance?: string
  readiness: number
  effective_score: number
  evidence_strength: string
  status: string
  sources: { source: string; score: number; activity_count: number }[]
}

export interface WhyBreakdownItem {
  skill: string
  importance: string
  weight_percent: number
  readiness: number
  effective_score: number
  evidence_strength: string
}

export interface RecommendationAction {
  title: string
  description: string
  reason: string
  skill: string | null
  priority: string
  href: string
  action_type: string
}

export interface MistakeItem {
  id: string
  source_type: string
  source_id: string
  title: string
  summary: string | null
  mistake_type: string
  occurrence_count: number
  status: string
  first_seen_at: string
  last_seen_at: string
  retry_href: string | null
  context: Record<string, unknown> | null
}

export interface MistakeSummary {
  open_count: number
  repeated_count: number
  resolved_count: number
  top_weak_topics: { title: string; count: number }[]
}

export interface JobMatch {
  coverage: number | null
  has_sufficient_mapping: boolean
  has_user_evidence?: boolean
  message: string | null
  required: { skill: string; readiness: number; status: string }[]
  preferred: { skill: string; readiness: number; status: string }[]
  why: { factor: string; weight_percent: number; score: number }[]
  evidence_strength?: string
}
