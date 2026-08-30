import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export interface InfraTrack {
  key: string
  label: string
  href: string
}

export interface InfraHome {
  domain: string
  tracks: InfraTrack[]
  continue: string | null
  weak_topics: string[]
  scenarios: Array<{
    slug: string
    title: string
    difficulty: string
    best_score: number
    status: string | null
  }>
  paths: Array<{ slug: string; title: string; href: string }>
  projects: Array<{ slug: string; title: string; href: string }>
  progress: InfraProgress
  unofficial_disclaimer: string
}

export interface InfraProgressTopic {
  key: string
  label: string
  mcq_attempts: number
  mcq_accuracy: number | null
  scenario_attempts: number
  scenario_best: number
}

export interface InfraProgress {
  domain: string
  topics: InfraProgressTopic[]
  weak_topics: string[]
  continue_href: string | null
  scenario_attempted: number
  scenario_mastered: number
  paths: Array<{ slug: string; title: string; href: string }>
  projects: Array<{ slug: string; title: string; href: string }>
}

export interface ScenarioCard {
  id: string
  slug: string
  title: string
  description: string
  domain_key: string
  scenario_type: string
  difficulty: string
  unofficial_cert_tag: string | null
  best_score: number
  status: string | null
}

export interface ScenarioDetail {
  id: string
  slug: string
  title: string
  description: string
  domain_key: string
  scenario_type: string
  difficulty: string
  context_text: string
  evidence_json: Record<string, unknown>
  unofficial_cert_tag: string | null
  unofficial_disclaimer: string
  mastery_threshold: number
  steps: Array<{
    id: string
    sort_order: number
    prompt: string
    context_snippet: string
    is_critical: boolean
    options: Array<{ id: string; label: string; sort_order: number }>
  }>
  best_score: number
  status: string | null
}

export interface ScenarioSubmitResponse {
  overall_score: number
  correct_decisions: number
  total_steps: number
  missed_critical: string[]
  explanation: string
  step_results: Array<{
    step_id: string
    option_id: string
    is_correct: boolean
    explanation: string
    is_critical: boolean
  }>
  mastered: boolean
  submission_id: string
}

export function fetchInfraHome(domain: 'cloud' | 'devops' | 'cybersecurity') {
  return apiClient.get<InfraHome>(apiEndpoints.infra.home(domain)).then((r) => r.data)
}

export function fetchInfraProgress(domain: 'cloud' | 'devops' | 'cybersecurity') {
  return apiClient.get<InfraProgress>(apiEndpoints.infra.progress(domain)).then((r) => r.data)
}

export function fetchScenarios(domain?: string) {
  const url = domain ? `${apiEndpoints.infra.scenarios}?domain=${domain}` : apiEndpoints.infra.scenarios
  return apiClient.get<ScenarioCard[]>(url).then((r) => r.data)
}

export function fetchScenario(slug: string) {
  return apiClient.get<ScenarioDetail>(apiEndpoints.infra.scenario(slug)).then((r) => r.data)
}

export function submitScenario(slug: string, answers: Array<{ step_id: string; option_id: string }>) {
  return apiClient
    .post<ScenarioSubmitResponse>(apiEndpoints.infra.scenarioSubmit(slug), { answers })
    .then((r) => r.data)
}

export function fetchAdminInfra(domain: 'cloud' | 'devops' | 'cybersecurity') {
  return apiClient.get<Record<string, unknown>>(apiEndpoints.admin.infraHome(domain)).then((r) => r.data)
}

export function fetchAdminScenarios() {
  return apiClient.get<Array<Record<string, unknown>>>(apiEndpoints.admin.scenarios).then((r) => r.data)
}

export function fetchAdminScenario(id: string) {
  return apiClient.get<Record<string, unknown>>(apiEndpoints.admin.scenario(id)).then((r) => r.data)
}

export function createAdminScenario(body: Record<string, unknown>) {
  return apiClient.post(apiEndpoints.admin.scenarios, body).then((r) => r.data)
}

export function updateAdminScenario(id: string, body: Record<string, unknown>) {
  return apiClient.patch(apiEndpoints.admin.scenario(id), body).then((r) => r.data)
}
