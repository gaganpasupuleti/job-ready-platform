import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export interface PracticePathCard {
  id: string
  slug: string
  title: string
  short_description: string
  path_type: string
  difficulty: string
  language: string | null
  estimated_minutes: number | null
  availability: string
  is_featured: boolean
  external_route: string | null
  item_count: number
  progress_percent: number
}

export interface ContinueLearningItem {
  kind: string
  title: string
  subtitle: string | null
  progress_percent: number
  href: string
  last_activity_at: string | null
}

export interface PracticeHubResponse {
  sections: Array<{ key: string; label: string; paths: PracticePathCard[] }>
  continue_learning: ContinueLearningItem[]
  recently_practiced: ContinueLearningItem[]
  recommended: PracticePathCard[]
}

export interface PracticePathDetail {
  id: string
  slug: string
  title: string
  short_description: string
  description: string | null
  path_type: string
  difficulty: string
  language: string | null
  availability: string
  external_route: string | null
  progress_percent: number
  sections: Array<{
    id: string
    title: string
    sort_order: number
    items: Array<{
      id: string
      item_type: string
      title: string | null
      href: string | null
      sort_order: number
      completed?: boolean
      coding_problem_id?: string | null
    }>
  }>
}

export interface CourseListItem {
  id: string
  slug: string
  title: string
  summary: string
  level: string
  primary_language_key: string | null
  lesson_count: number
  progress_percent: number
  is_featured: boolean
}

export interface LessonNavItem {
  id: string
  slug: string
  title: string
  lesson_type: string
  sort_order: number
  status: string
  module_slug: string
  module_title: string
}

export interface CourseDetail {
  id: string
  slug: string
  title: string
  summary: string
  level: string
  progress_percent: number
  status: string
  continue_href: string | null
  modules: Array<{
    id: string
    slug: string
    title: string
    sort_order: number
    summary: string | null
    lessons: LessonNavItem[]
    completed_count: number
    lesson_count: number
  }>
}

export interface LessonDetail {
  id: string
  slug: string
  title: string
  lesson_type: string
  statement_json: {
    blocks?: Array<{ type: string; value?: string; language?: string; title?: string; items?: string[]; tone?: string }>
  }
  starter_code: Record<string, string>
  coding_problem_id: string | null
  coding_problem_slug: string | null
  status: string
  attempts: number
  solution_unlocked: boolean
  solution_json: {
    explanation?: string
    code?: string
    language?: string
    python?: string
    javascript?: string
  } | null
  hints: Array<{ id: string; hint_text: string; sort_order: number; unlocked: boolean }>
  doubts: Array<{ id: string; question: string; answer: string; sort_order: number }>
  resources: Array<{ id: string; resource_type: string; title: string; url: string; description: string | null }>
  steps: Array<{ id: string; title: string; body_md: string; sort_order: number }>
  progress_blocks: LessonNavItem[]
  prev_href: string | null
  next_href: string | null
  course_slug: string
  course_title?: string | null
  module_slug: string
  module_title?: string | null
  course_percent?: number
  lesson_index?: number
  lesson_total?: number
  primary_language_key?: string | null
  completion_requires_submit: boolean
  can_mark_complete: boolean
}

export interface ProjectCard {
  id: string
  slug: string
  title: string
  short_description: string
  difficulty: string
  technology: string | null
  category_key: string
  availability: string
  estimated_minutes: number | null
  task_count: number
  progress_percent: number
  href: string
}

export interface ProjectDetail {
  id: string
  slug: string
  title: string
  short_description: string
  description: string | null
  difficulty: string
  technology: string | null
  category_key: string
  availability: string
  estimated_minutes: number | null
  prerequisites: string[]
  skills: string[]
  final_objective: string | null
  progress_percent: number
  status: string
  completed_task_count: number
  task_count: number
  current_task_id: string | null
  current_task_href: string | null
  continue_href: string | null
  modules: Array<{
    id: string
    title: string
    sort_order: number
    tasks: Array<{
      id: string
      title: string
      sort_order: number
      summary: string | null
      task_type: string
      status: string
      href: string | null
      engine_href?: string | null
      workspace_href?: string | null
      coding_problem_id?: string | null
      sql_problem_id?: string | null
      topic_id?: string | null
      scenario_slug?: string | null
      checklist_json: unknown[]
      checklist_state?: Record<string, boolean>
      body_json: Record<string, unknown>
      estimated_minutes?: number | null
    }>
  }>
}

export interface ProjectTaskPage {
  project_id: string
  project_slug: string
  project_title: string
  project_percent: number
  project_completed: boolean
  skills: string[]
  estimated_minutes: number | null
  completed_at: string | null
  prev_task_id: string | null
  next_task_id: string | null
  task: ProjectDetail['modules'][0]['tasks'][0]
}

export async function fetchPracticeHub() {
  const { data } = await apiClient.get<PracticeHubResponse>(apiEndpoints.learn.practiceHub)
  return data
}

export async function fetchPracticePath(slug: string) {
  const { data } = await apiClient.get<PracticePathDetail>(apiEndpoints.learn.path(slug))
  return data
}

export async function searchPractice(q: string) {
  const { data } = await apiClient.get<{ items: Array<{ kind: string; title: string; subtitle: string | null; href: string }> }>(
    apiEndpoints.learn.search,
    { params: { q } },
  )
  return data
}

export async function fetchCourses() {
  const { data } = await apiClient.get<CourseListItem[]>(apiEndpoints.learn.courses)
  return data
}

export async function fetchCourse(slug: string) {
  const { data } = await apiClient.get<CourseDetail>(apiEndpoints.learn.course(slug))
  return data
}

export async function fetchLesson(course: string, module: string, lesson: string) {
  const { data } = await apiClient.get<LessonDetail>(apiEndpoints.learn.lesson(course, module, lesson))
  return data
}

export async function startLesson(id: string) {
  const { data } = await apiClient.post(apiEndpoints.learn.lessonStart(id))
  return data
}

export async function completeLesson(id: string) {
  const { data } = await apiClient.post<{ status: string; next_href?: string }>(
    apiEndpoints.learn.lessonComplete(id),
  )
  return data
}

export async function recordLessonAttempt(id: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post(apiEndpoints.learn.lessonAttempt(id), payload)
  return data
}

export async function sendLessonFeedback(
  id: string,
  payload: { vote?: string; report_issue?: boolean; note?: string },
) {
  const { data } = await apiClient.post(apiEndpoints.learn.lessonFeedback(id), payload)
  return data
}

export async function fetchProjects() {
  const { data } = await apiClient.get<ProjectCard[]>(apiEndpoints.learn.projects)
  return data
}

export async function fetchProject(slug: string) {
  const { data } = await apiClient.get<ProjectDetail>(apiEndpoints.learn.project(slug))
  return data
}

export async function startProject(id: string) {
  const { data } = await apiClient.post<{ status: string; percent: number; href: string }>(
    apiEndpoints.learn.projectStart(id),
  )
  return data
}

export async function completeProjectTask(projectId: string, taskId: string) {
  const { data } = await apiClient.post(apiEndpoints.learn.projectTaskComplete(projectId, taskId))
  return data
}

export async function fetchProjectTask(slug: string, taskId: string) {
  const { data } = await apiClient.get<ProjectTaskPage>(apiEndpoints.learn.projectTask(slug, taskId))
  return data
}

export async function updateProjectTaskChecklist(projectId: string, taskId: string, checked: Record<string, boolean>) {
  const { data } = await apiClient.patch(apiEndpoints.learn.projectTaskChecklist(projectId, taskId), { checked })
  return data
}

export async function startPath(id: string) {
  const { data } = await apiClient.post(apiEndpoints.learn.pathStart(id))
  return data
}

export async function completePathItem(pathId: string, itemId: string) {
  const { data } = await apiClient.post(apiEndpoints.learn.pathItemComplete(pathId, itemId))
  return data
}

export async function fetchContinueLearning() {
  const { data } = await apiClient.get<ContinueLearningItem[]>(apiEndpoints.learn.continueLearning)
  return data
}

export async function fetchAdminPracticePaths() {
  const { data } = await apiClient.get<Array<Record<string, unknown>>>(apiEndpoints.admin.practicePaths)
  return data
}

export async function fetchAdminCourses() {
  const { data } = await apiClient.get<Array<Record<string, unknown>>>(apiEndpoints.admin.learnCourses)
  return data
}

export async function patchAdminCourse(id: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.patch(apiEndpoints.admin.learnCourse(id), payload)
  return data
}

export async function patchAdminPath(id: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.patch(apiEndpoints.admin.practicePath(id), payload)
  return data
}
