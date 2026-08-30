export interface HealthChecks {
  database?: string
  redis?: string
  sql_sandbox?: string
  judge0?: string
}

export interface HealthResponse {
  status: string
  service: string
  checks?: HealthChecks
}

export interface PlatformModule {
  id: string
  name: string
  category: string
  enabled: boolean
  route: string | null
}

export interface ModulesResponse {
  modules: PlatformModule[]
}

export interface NavItem {
  label: string
  path: string
  icon?: string
}

export interface NavSection {
  title: string
  items: NavItem[]
}

export interface DashboardCard {
  id: string
  title: string
  value: string
  subtitle?: string
  trend?: string
  trendDirection?: 'up' | 'down' | 'neutral'
}

export interface WeakSkill {
  skill: string
  score: number
}

export interface UpcomingAssessment {
  id: string
  title: string
  date: string
  type: string
}
