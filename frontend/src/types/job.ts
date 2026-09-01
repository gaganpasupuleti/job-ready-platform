export type JobSourceType = 'manual' | 'import' | 'donor' | 'api' | 'career_site'
export type JobStatus = 'active' | 'expired' | 'archived'
export type JobSkillImportance = 'required' | 'preferred' | 'mentioned'
export type WorkMode = 'remote' | 'hybrid' | 'onsite' | 'unknown'
export type EmploymentType = 'full_time' | 'part_time' | 'contract' | 'internship' | 'unknown'
export type ApplicationStatus =
  | 'saved'
  | 'preparing'
  | 'applied'
  | 'screening'
  | 'assessment'
  | 'interview'
  | 'offer'
  | 'rejected'
  | 'withdrawn'
  | 'accepted'
  | 'ghosted'
export type ApplicationPriority = 'low' | 'medium' | 'high'
export type IngestionRunStatus = 'running' | 'completed' | 'failed' | 'partial'

export interface JobSkillPublic {
  id: string
  name: string
  slug: string
  importance: JobSkillImportance
}

export interface JobRolePublic {
  id: string
  name: string
  slug: string
  mapping_source: string | null
}

export interface JobCard {
  id: string
  slug: string
  title: string
  company_name: string
  company_slug: string | null
  location_text: string | null
  work_mode: WorkMode | null
  employment_type: EmploymentType | null
  experience_min_years: number | null
  experience_max_years: number | null
  posted_at: string | null
  status: JobStatus
  is_remote: boolean | null
  top_skills: string[]
  is_saved: boolean
}

export interface JobListResponse {
  items: JobCard[]
  total: number
  page: number
  limit: number
}

export interface JobPracticeLink {
  label: string
  path: string
  reason: string | null
}

export interface JobDetail {
  id: string
  slug: string
  title: string
  company_name: string
  company_slug: string | null
  company_id: string | null
  description: string
  requirements_text: string | null
  responsibilities_text: string | null
  employment_type: EmploymentType | null
  work_mode: WorkMode | null
  experience_min_years: number | null
  experience_max_years: number | null
  salary_min: string | null
  salary_max: string | null
  salary_currency: string | null
  location_text: string | null
  country: string | null
  state: string | null
  city: string | null
  source_url: string | null
  apply_url: string | null
  posted_at: string | null
  expires_at: string | null
  status: JobStatus
  is_remote: boolean | null
  source_name: string | null
  skills: JobSkillPublic[]
  roles: JobRolePublic[]
  is_saved: boolean
  application_id: string | null
  application_status: ApplicationStatus | null
  practice_links: JobPracticeLink[]
  interview_prep_url: string | null
  company_prep_url: string | null
}

export interface SavedJobItem {
  id: string
  job_id: string
  saved_at: string
  job: JobCard
}

export interface ApplicationSummary {
  id: string
  job_id: string
  job_title: string
  company_name: string
  status: ApplicationStatus
  applied_at: string | null
  next_follow_up_at: string | null
  priority: ApplicationPriority
  job_status: JobStatus
}

export interface ApplicationDetail {
  id: string
  job_id: string
  status: ApplicationStatus
  applied_at: string | null
  next_follow_up_at: string | null
  source_of_application: string | null
  application_url: string | null
  notes: string | null
  salary_expected: string | null
  priority: ApplicationPriority
  created_at: string
  updated_at: string
  job: JobDetail
}

export interface ApplicationStatusHistoryItem {
  id: string
  from_status: ApplicationStatus | null
  to_status: ApplicationStatus
  note: string | null
  changed_at: string
}

export interface ApplicationUpdate {
  status?: ApplicationStatus
  next_follow_up_at?: string | null
  notes?: string | null
  salary_expected?: string | null
  priority?: ApplicationPriority
  application_url?: string | null
  source_of_application?: string | null
}

export interface ApplicationStatusChange {
  to_status: ApplicationStatus
  note?: string | null
}

export interface JobsSummary {
  saved_count: number
  applications_total: number
  applied_count: number
  interview_count: number
  offer_count: number
  rejected_count: number
  follow_ups_due: number
  follow_ups_today: number
  follow_ups_overdue: number
}

export interface JobPreferenceUpdate {
  target_role_slug?: string | null
  preferred_locations?: string[] | null
  remote_preference?: WorkMode | null
}

export interface JobSourcePublic {
  id: string
  name: string
  slug: string
  source_type: JobSourceType
  is_active: boolean
}

export interface AdminJobCreate {
  title: string
  company_name: string
  description: string
  requirements_text?: string | null
  responsibilities_text?: string | null
  employment_type?: EmploymentType | null
  work_mode?: WorkMode | null
  experience_min_years?: number | null
  experience_max_years?: number | null
  location_text?: string | null
  city?: string | null
  state?: string | null
  country?: string | null
  is_remote?: boolean | null
  source_url?: string | null
  apply_url?: string | null
  posted_at?: string | null
  expires_at?: string | null
  skills?: string[]
  roles?: string[]
  status?: JobStatus
}

export interface AdminJobUpdate {
  title?: string
  company_name?: string
  description?: string
  requirements_text?: string | null
  responsibilities_text?: string | null
  employment_type?: EmploymentType | null
  work_mode?: WorkMode | null
  experience_min_years?: number | null
  experience_max_years?: number | null
  location_text?: string | null
  city?: string | null
  state?: string | null
  country?: string | null
  is_remote?: boolean | null
  source_url?: string | null
  apply_url?: string | null
  posted_at?: string | null
  expires_at?: string | null
  skills?: string[] | null
  roles?: string[] | null
  status?: JobStatus | null
}

export interface ImportPreviewRow {
  row_number: number
  title: string
  company: string
  action: string
  errors: string[]
}

export interface ImportPreviewResponse {
  run_id: string | null
  rows: ImportPreviewRow[]
  valid_count: number
  error_count: number
  create_count: number
  update_count: number
  duplicate_count: number
}

export interface ImportConfirmRequest {
  preview_id: string
  filename?: string | null
}

export interface ImportConfirmResponse {
  run_id: string
  status: IngestionRunStatus
  records_created: number
  records_updated: number
  records_skipped: number
  records_failed: number
}

export interface IngestionRunPublic {
  id: string
  source_id: string | null
  source_name: string | null
  started_at: string
  completed_at: string | null
  status: IngestionRunStatus
  records_seen: number
  records_created: number
  records_updated: number
  records_skipped: number
  records_failed: number
  source_file_name: string | null
}

export interface IngestionErrorPublic {
  id: string
  row_number: number | null
  external_id: string | null
  error_type: string
  message: string
}

export interface AdminJobListResponse {
  items: JobCard[]
  total: number
  page: number
  limit: number
}

export interface JobListFilters {
  q?: string
  role?: string
  skill?: string
  company?: string
  city?: string
  state?: string
  country?: string
  remote?: boolean
  work_mode?: string
  employment_type?: string
  experience_min?: number
  posted_within_days?: number
  sort?: string
  page?: number
  limit?: number
}
