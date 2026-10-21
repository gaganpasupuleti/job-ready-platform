import { moreMenuGroups, primaryNavItems } from '@/components/navigation/navConfig'

export type ExploreCategoryId = 'practice' | 'career' | 'ai' | 'admin'

export interface ExploreDestination {
  path: string
  label: string
  description: string
  category: ExploreCategoryId
  adminOnly?: boolean
  match?: string[]
}

export const exploreCategoryLabels: Record<ExploreCategoryId, string> = {
  practice: 'Practice',
  career: 'Career',
  ai: 'AI & Engineering',
  admin: 'Admin',
}

const groupCategory: Record<string, ExploreCategoryId> = {
  Practice: 'practice',
  Career: 'career',
  'AI & Engineering': 'ai',
}

const pathMatchers: Record<string, string[]> = {
  '/practice/aptitude': ['/practice/aptitude', '/practice/sessions', '/assessments'],
  '/roadmaps': ['/roadmaps'],
  '/jobs/recommended': ['/jobs/recommended'],
  '/jobs/applications': ['/jobs/applications', '/jobs/preferences'],
  '/ai': ['/ai'],
  '/reports': ['/reports'],
}

function fromMoreMenu(): ExploreDestination[] {
  return moreMenuGroups.flatMap((group) =>
    group.items.map((item) => ({
      path: item.path,
      label: item.label,
      description: item.label,
      category: groupCategory[group.title] ?? 'career',
      match: pathMatchers[item.path],
    })),
  )
}

const adminDestinations: ExploreDestination[] = [
  {
    path: '/admin/questions',
    label: 'Question bank',
    description: 'Manage assessment questions',
    category: 'admin',
    adminOnly: true,
    match: ['/admin/questions'],
  },
  {
    path: '/admin/library',
    label: 'Library admin',
    description: 'Curate library resources',
    category: 'admin',
    adminOnly: true,
    match: ['/admin/library'],
  },
  {
    path: '/admin/feedback',
    label: 'Student feedback',
    description: 'Review learner feedback',
    category: 'admin',
    adminOnly: true,
    match: ['/admin/feedback'],
  },
]

export const exploreDestinations: ExploreDestination[] = [...fromMoreMenu(), ...adminDestinations]

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
  const order: ExploreCategoryId[] = ['practice', 'career', 'ai', 'admin']
  return order.filter((id) => visible.some((d) => d.category === id))
}
