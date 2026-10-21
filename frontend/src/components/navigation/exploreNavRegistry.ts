import { primaryNavItems } from '@/components/navigation/navConfig'

export type ExploreCategoryId = 'practice' | 'learning' | 'career' | 'ai' | 'admin'

export interface ExploreDestination {
  path: string
  label: string
  description: string
  category: ExploreCategoryId
  adminOnly?: boolean
  /** Longest-prefix matchers; defaults to [path]. */
  match?: string[]
}

export const exploreCategoryLabels: Record<ExploreCategoryId, string> = {
  practice: 'Practice',
  learning: 'Learning',
  career: 'Career',
  ai: 'AI & Engineering',
  admin: 'Admin',
}

/** Destinations shown in Explore (not duplicated in the primary masthead). */
export const exploreDestinations: ExploreDestination[] = [
  { path: '/practice/sql', label: 'SQL', description: 'Query practice with runnable exercises.', category: 'practice' },
  { path: '/practice/dsa', label: 'DSA', description: 'Data structures and algorithms drills.', category: 'practice' },
  { path: '/practice/coding', label: 'Coding', description: 'Language coding challenges.', category: 'practice' },
  { path: '/practice/typing', label: 'Typing', description: 'Speed and accuracy training.', category: 'practice' },
  { path: '/practice/mcq', label: 'Technical MCQs', description: 'Multiple-choice technical review.', category: 'practice' },
  { path: '/practice/aptitude', label: 'Aptitude / CRT', description: 'Campus aptitude and CRT prep.', category: 'practice', match: ['/practice/aptitude', '/practice/sessions', '/assessments'] },
  {
    path: '/practice/python',
    label: 'Python playground',
    description: 'Run Python in the browser.',
    category: 'learning',
    match: ['/practice/python'],
  },
  {
    path: '/practice/compiler',
    label: 'Compiler lab',
    description: 'Try code in supported languages.',
    category: 'learning',
    match: ['/practice/compiler'],
  },
  {
    path: '/practice/projects',
    label: 'Projects',
    description: 'Guided project briefs and submissions.',
    category: 'career',
    match: ['/practice/projects'],
  },
  { path: '/roadmaps', label: 'Career roadmaps', description: 'Official skill roadmaps with topics and articles.', category: 'career', match: ['/roadmaps'] },
  { path: '/support/requests', label: 'My requests', description: 'Support tickets you have opened.', category: 'career' },
  { path: '/readiness', label: 'Job readiness', description: 'Readiness score and recommendations.', category: 'career' },
  { path: '/interviews', label: 'Interview prep', description: 'Interview practice and resources.', category: 'career' },
  { path: '/bookmarks', label: 'Bookmarks', description: 'Saved problems and resources.', category: 'career' },
  { path: '/jobs/recommended', label: 'Recommended jobs', description: 'Roles matched to your profile.', category: 'career', match: ['/jobs/recommended'] },
  { path: '/jobs/applications', label: 'Applications', description: 'Track jobs you applied to.', category: 'career', match: ['/jobs/applications', '/jobs/preferences'] },
  { path: '/ai', label: 'AI home', description: 'AI learning hub and tools.', category: 'ai', match: ['/ai'] },
  { path: '/ai/prompt-engineering', label: 'Prompt engineering', description: 'Prompt patterns and exercises.', category: 'ai' },
  { path: '/cloud', label: 'Cloud', description: 'Cloud fundamentals track.', category: 'ai' },
  { path: '/devops', label: 'DevOps', description: 'CI/CD and operations topics.', category: 'ai' },
  { path: '/cybersecurity', label: 'Cybersecurity', description: 'Security concepts and labs.', category: 'ai' },
  {
    path: '/admin/questions',
    label: 'Question bank',
    description: 'Manage assessment questions.',
    category: 'admin',
    adminOnly: true,
    match: ['/admin/questions'],
  },
  {
    path: '/admin/library',
    label: 'Library admin',
    description: 'Publish and curate library resources.',
    category: 'admin',
    adminOnly: true,
    match: ['/admin/library'],
  },
  {
    path: '/admin/feedback',
    label: 'Student feedback',
    description: 'Review learner feedback.',
    category: 'admin',
    adminOnly: true,
    match: ['/admin/feedback'],
  },
]

const primaryPrefixes = primaryNavItems.flatMap((item) => item.match ?? [item.path])

function isPrimaryOnlyPath(path: string) {
  return primaryPrefixes.some((prefix) => {
    if (prefix === '/') return path === '/'
    return path === prefix
  })
}

export function visibleExploreDestinations(isAdmin: boolean) {
  return exploreDestinations.filter((dest) => {
    if (dest.adminOnly && !isAdmin) return false
    if (isPrimaryOnlyPath(dest.path)) return false
    return true
  })
}

function matchersFor(dest: ExploreDestination) {
  return dest.match ?? [dest.path]
}

export function resolveExploreDestination(pathname: string, isAdmin: boolean): ExploreDestination | null {
  const visible = visibleExploreDestinations(isAdmin)
  const hits = visible.filter((dest) =>
    matchersFor(dest).some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)),
  )
  if (hits.length === 0) return null
  return hits.reduce((best, dest) => {
    const bestLen = Math.max(...matchersFor(best).map((p) => (pathname.startsWith(p) ? p.length : 0)))
    const destLen = Math.max(...matchersFor(dest).map((p) => (pathname.startsWith(p) ? p.length : 0)))
    return destLen > bestLen ? dest : best
  })
}

export function isExploreRouteActive(pathname: string, isAdmin: boolean) {
  return resolveExploreDestination(pathname, isAdmin) !== null
}

export function categoryForPath(pathname: string, isAdmin: boolean): ExploreCategoryId {
  return resolveExploreDestination(pathname, isAdmin)?.category ?? 'practice'
}

export function filterExploreDestinations(query: string, isAdmin: boolean) {
  const q = query.trim().toLowerCase()
  const visible = visibleExploreDestinations(isAdmin)
  if (!q) return visible
  return visible.filter(
    (dest) =>
      dest.label.toLowerCase().includes(q) ||
      dest.description.toLowerCase().includes(q) ||
      dest.path.toLowerCase().includes(q),
  )
}

export function exploreCategoriesForUser(isAdmin: boolean): ExploreCategoryId[] {
  const visible = visibleExploreDestinations(isAdmin)
  const order: ExploreCategoryId[] = ['practice', 'learning', 'career', 'ai', 'admin']
  return order.filter((id) => visible.some((d) => d.category === id))
}
