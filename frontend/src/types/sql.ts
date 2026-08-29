export type Difficulty = 'easy' | 'medium' | 'hard'

export type SqlProgressStatus = 'unsolved' | 'attempted' | 'solved'

export type SqlSubmissionStatus =
  | 'accepted'
  | 'wrong_answer'
  | 'sql_error'
  | 'timeout'
  | 'execution_disabled'
  | 'internal_error'

export type SqlDialect = 'postgresql'

export interface SqlColumnSchema {
  column_name: string
  data_type: string
  is_nullable: boolean
  sort_order: number
}

export interface SqlTableSchemaPublic {
  table_name: string
  display_name?: string | null
  description?: string | null
  columns: SqlColumnSchema[]
}

export interface SqlTablePreview {
  table_name: string
  columns: string[]
  rows: unknown[][]
  truncated: boolean
}

export interface SqlProblemListItem {
  id: string
  slug: string
  title: string
  difficulty: Difficulty
  topic_id: string
  topic_name?: string | null
  topic_slug?: string | null
  tags?: string[]
  role_tags?: string[]
  estimated_time_seconds?: number
  progress_status?: SqlProgressStatus | null
  acceptance_rate?: number | null
  attempt_count?: number | null
}

export interface SqlProblemDetail {
  id: string
  slug: string
  title: string
  description: string
  difficulty: Difficulty
  database_dialect: SqlDialect
  topic_id: string
  topic_name?: string | null
  topic_slug?: string | null
  tags?: string[]
  role_tags?: string[]
  scenario?: string | null
  task_description: string
  expected_columns: string[]
  sample_expected_rows: unknown[][]
  hints: string[]
  estimated_time_seconds: number
  order_sensitive: boolean
  schema_tables: SqlTableSchemaPublic[]
  progress_status?: SqlProgressStatus | null
  bookmarked: boolean
  solution_unlocked: boolean
  execution_available: boolean
}

export interface SqlRunResponse {
  columns: string[]
  rows: unknown[][]
  row_count: number
  execution_time_ms?: number | null
  truncated: boolean
  error?: string | null
  status: string
}

export interface SqlSubmitResponse {
  submission_id?: string | null
  status: SqlSubmissionStatus
  message: string
  execution_time_ms?: number | null
  result_row_count?: number | null
  feedback?: Record<string, unknown> | null
  columns: string[]
  rows: unknown[][]
  truncated: boolean
  error?: string | null
  solution_unlocked: boolean
}

export interface SqlSubmissionListItem {
  id: string
  problem_id: string
  problem_slug: string
  problem_title: string
  difficulty?: Difficulty | null
  topic_name?: string | null
  status: SqlSubmissionStatus
  result_row_count?: number | null
  execution_time_ms?: number | null
  submitted_at: string
}

export interface SqlSubmissionDetail {
  id: string
  problem_id: string
  problem_slug: string
  problem_title: string
  difficulty?: Difficulty | null
  query_text: string
  status: SqlSubmissionStatus
  result_row_count?: number | null
  execution_time_ms?: number | null
  error_message?: string | null
  feedback?: Record<string, unknown> | null
  submitted_at: string
}

export interface DifficultyBreakdown {
  solved: number
  total: number
  attempted: number
}

export interface TopicBreakdown {
  topic_slug: string
  topic_name: string
  solved: number
  total: number
}

export interface SqlProgressSummary {
  total_problems: number
  solved_count: number
  attempted_count: number
  easy?: DifficultyBreakdown
  medium?: DifficultyBreakdown
  hard?: DifficultyBreakdown
  topics?: TopicBreakdown[]
}

export interface SqlSolutionResponse {
  solution_query: string
  solution_explanation?: string | null
  alternate_solution?: string | null
  key_concepts: string[]
}

export interface SqlExecutionStatus {
  available: boolean
  dialect?: string
  message?: string | null
  timeout_ms?: number | null
  max_rows?: number | null
}

export interface AdminSqlColumnInput {
  column_name: string
  data_type: string
  is_nullable?: boolean
  sort_order?: number
}

export interface AdminSqlTableInput {
  table_name: string
  display_name?: string | null
  description?: string | null
  sort_order?: number
  columns: AdminSqlColumnInput[]
  rows: Record<string, unknown>[]
}

export interface AdminSqlProblemDetail {
  id: string
  slug: string
  title: string
  description: string
  difficulty: Difficulty
  database_dialect: SqlDialect
  domain_id: string
  category_id: string
  topic_id: string
  subtopic_id?: string | null
  tags: string[]
  role_tags: string[]
  scenario?: string | null
  task_description: string
  expected_columns: string[]
  order_sensitive: boolean
  solution_query: string
  solution_explanation?: string | null
  alternate_solution?: string | null
  key_concepts: string[]
  hints: string[]
  sample_expected_rows: unknown[][]
  estimated_time_seconds: number
  is_active: boolean
  is_sample: boolean
  tables: AdminSqlTableInput[]
  expected_rows: unknown[][]
}

export interface AdminSqlValidateResponse {
  valid: boolean
  errors: string[]
  warnings: string[]
  solution_columns: string[]
  solution_row_count?: number | null
}
