export type Difficulty = 'easy' | 'medium' | 'hard'

export type ProblemProgressStatus = 'unsolved' | 'attempted' | 'solved'

export type SubmissionStatus =

  | 'pending'

  | 'running'

  | 'accepted'

  | 'wrong_answer'

  | 'time_limit_exceeded'

  | 'memory_limit_exceeded'

  | 'runtime_error'

  | 'compilation_error'

  | 'internal_error'



export interface LanguageInfo {
  id: number
  name: string
  key?: string
  available?: boolean
}



export interface CodingProblemListItem {

  id: string

  slug: string

  title: string

  difficulty: Difficulty

  domain_id: string

  category_id: string

  topic_id: string

  topic_name?: string | null

  topic_slug?: string | null

  tags?: string[]

  attempts?: number | null

  acceptance_rate?: number | null

  supported_language_ids?: number[]

  progress_status?: ProblemProgressStatus | null

}



export interface SampleTestCase {

  id: string

  name: string | null

  input: string

  expected_output: string

  explanation?: string | null

}



export interface CodingProblemDetail {

  id: string

  slug: string

  title: string

  description: string

  difficulty: Difficulty

  constraints: string | null

  input_format?: string | null

  output_format?: string | null

  tags?: string[]

  time_limit_ms: number

  memory_limit_kb: number

  starter_code: Record<string, string>

  sample_test_cases: SampleTestCase[]

  supported_languages: LanguageInfo[]

  progress_status?: ProblemProgressStatus | null

  bookmarked?: boolean

  execution_available?: boolean

}



export interface TestResult {

  test_number: number

  name?: string | null

  status: SubmissionStatus

  input?: string | null

  expected_output?: string | null

  stdout?: string | null

  stderr?: string | null

  execution_time_ms?: number | null

  memory_kb?: number | null

  is_hidden: boolean

}



export interface ExecutionResponse {

  submission_id?: string | null

  submission_type: 'run' | 'submit'

  status: SubmissionStatus

  passed_tests: number

  total_tests: number

  execution_time_ms?: number | null

  memory_kb?: number | null

  results: TestResult[]

}



export interface SubmissionListItem {

  id: string

  problem_id: string

  problem_title: string

  problem_difficulty?: Difficulty | null

  language_id?: number

  language_name: string

  submission_type: 'run' | 'submit'

  status: SubmissionStatus

  passed_tests: number

  total_tests: number

  execution_time_ms?: number | null

  created_at: string

}



export interface SubmissionDetail extends ExecutionResponse {

  id: string

  problem_id: string

  problem_title: string

  problem_difficulty?: Difficulty | null

  source_code: string

  language_id: number

  language_name: string

  created_at: string

  hidden_summary?: string | null

}



export interface DifficultyBreakdown {

  solved: number

  total: number

  attempted: number

}



export interface CodingProgressSummary {

  total_problems: number

  solved_count: number

  attempted_count: number

  easy?: DifficultyBreakdown

  medium?: DifficultyBreakdown

  hard?: DifficultyBreakdown

  items: CodingProblemListItem[]

}



export interface ExecutionStatusResponse {
  enabled?: boolean
  available: boolean
  provider?: string
  message?: string | null
  languages?: LanguageInfo[]
}



export interface CodingBookmarkItem {

  id: string

  slug: string

  title: string

  difficulty: Difficulty

  topic_name?: string | null

  bookmarked_at: string

}



export interface AdminTestCase {

  id?: string

  name?: string | null

  input: string

  expected_output: string

  is_hidden: boolean

  is_sample: boolean

  sort_order?: number

  explanation?: string | null

}



export interface AdminCodingProblemDetail {

  id: string

  slug: string

  title: string

  description: string

  difficulty: Difficulty

  domain_id: string

  category_id: string

  topic_id: string

  constraints: string | null

  input_format?: string | null

  output_format?: string | null

  tags?: string[]

  time_limit_ms: number

  memory_limit_kb: number

  starter_code: Record<string, string>

  supported_language_ids?: number[]

  is_active: boolean

  is_sample: boolean

  test_cases: (AdminTestCase & { id: string; problem_id: string })[]

}

