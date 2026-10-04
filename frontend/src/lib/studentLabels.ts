const LESSON_TYPES: Record<string, string> = {
  reading: 'Reading',
  article: 'Article',
  video: 'Video',
  practice: 'Practice',
  quiz: 'Quiz',
  interactive_code: 'Code exercise',
  worked_example: 'Worked example',
}

const SOURCE_TYPES: Record<string, string> = {
  all: 'All',
  mcq: 'MCQ',
  sql: 'SQL',
  coding: 'Coding',
  prompt: 'Prompt',
  scenario: 'Scenario',
  interview: 'Interview',
}

const STATUSES: Record<string, string> = {
  recent: 'Recent',
  repeated: 'Repeated',
  unresolved: 'Unresolved',
  resolved: 'Resolved',
  reviewed: 'Reviewed',
  open: 'Open',
  not_started: 'Not started',
  in_progress: 'In progress',
  attempted: 'Attempted',
  unsolved: 'Not started',
  solved: 'Solved',
  completed: 'Completed',
  locked: 'Locked',
  mastered: 'Mastered',
}

/** Student-facing label. Snake-case values get a readable fallback; other text is left as written. */
export function humanLabel(value: string | null | undefined, dictionary?: Record<string, string>): string {
  if (!value || !value.trim()) return 'Not set'
  const key = value.trim().toLowerCase()
  const known = dictionary?.[key]
  if (known) return known
  if (/^[a-z0-9]+(?:_[a-z0-9]+)*$/.test(key)) {
    return key
      .split('_')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ')
  }
  return value.trim()
}

export function lessonTypeLabel(value: string | null | undefined) {
  return humanLabel(value, LESSON_TYPES)
}

export function sourceTypeLabel(value: string | null | undefined) {
  return humanLabel(value, SOURCE_TYPES)
}

export function statusLabelText(value: string | null | undefined) {
  return humanLabel(value, STATUSES)
}

const MATERIAL_KINDS: Record<string, string> = {
  article: 'Article',
  cheat_sheet: 'Cheat sheet',
  cheatsheet: 'Cheat sheet',
  guide: 'Guide',
  reading: 'Reading',
}

export function materialKindLabel(value: string | null | undefined) {
  return humanLabel(value, MATERIAL_KINDS)
}

/** Several track cards can point at one catalog. Say so instead of implying separate content. */
export function sharedDestinationNote(
  href: string | null | undefined,
  hrefs: Array<string | null | undefined>,
): string | null {
  const path = (href ?? '').split('?')[0].replace(/\/$/, '')
  if (!path) return null
  const count = hrefs.filter((item) => (item ?? '').split('?')[0].replace(/\/$/, '') === path).length
  return count > 1 ? 'Several tracks open this same catalog. The topic focus differs.' : null
}

const RESULTS_HREF = /^\/practice\/sessions\/[^/]+\/results\/?$/

/** MCQ mistake links point at a finished results page. That is not a new attempt. */
export function mistakeAction(href: string | null | undefined): {
  href: string
  label: string
  note: string | null
} | null {
  if (!href) return null
  if (RESULTS_HREF.test(href)) {
    return {
      href,
      label: 'View results',
      note: 'Incorrect questions cannot be retried as a new session. This opens the saved results.',
    }
  }
  return { href, label: 'Retry', note: null }
}

export interface MistakeLike {
  source_type?: string | null
  status?: string | null
  title?: string | null
  occurrence_count?: number | null
}

/** Weak-topic copy for a SQL page. Topics from other subjects are ignored. */
export function sqlWeakTopic(
  mistakes: MistakeLike[] | null | undefined,
): null | { empty: true } | { empty: false; title: string; count: number } {
  if (!mistakes) return null
  const open = mistakes.filter((item) => item.source_type === 'sql' && item.status !== 'resolved')
  if (open.length === 0) return { empty: true }
  const counts = new Map<string, number>()
  for (const item of open) {
    const title = item.title?.trim()
    if (!title) continue
    counts.set(title, (counts.get(title) ?? 0) + (item.occurrence_count || 1))
  }
  const top = [...counts.entries()].sort((left, right) => right[1] - left[1])[0]
  if (!top) return { empty: true }
  return { empty: false, title: top[0], count: top[1] }
}

/** A count from a failed or missing payload stays unknown. */
export function knownCount(value: number | null | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) ? String(value) : '—'
}

/** A percent is shown only when the payload included a finite number. */
export function knownPercent(value: number | null | undefined): string | null {
  return typeof value === 'number' && Number.isFinite(value) ? `${value}%` : null
}

/** Prefer a real topic name. A long question sentence is not a topic label. */
export function reviewTopicLabel(item: {
  title?: string | null
  context?: Record<string, unknown> | null
}): string {
  const topic = item.context?.topic_name
  if (typeof topic === 'string' && topic.trim()) return topic.trim()
  const title = item.title?.trim() ?? ''
  if (!title || title.length > 72) return 'Topic not labeled'
  return title
}

/** Global weak topics are not restated as if they belonged to the active subject filter. */
export function showGlobalWeakTopics(sourceFilter: string): boolean {
  return sourceFilter === 'all'
}

export function jobsRecommendationCopy(input: {
  preferencesError: boolean
  configured: boolean
  targetName?: string | null
  scored: boolean
  hasItems: boolean
}): { summary: string; showPreferencesLink: boolean } {
  if (input.preferencesError) {
    return {
      summary: 'Job preferences could not be loaded, so this list is not labeled as a personal match.',
      showPreferencesLink: false,
    }
  }
  if (input.configured && input.scored) {
    return {
      summary: `Openings related to ${input.targetName}. Requirement coverage is not a hiring probability.`,
      showPreferencesLink: false,
    }
  }
  if (input.configured) {
    return {
      summary: input.hasItems
        ? 'A scored match is not available for your target role yet. These are recent openings from the catalog, not personalized recommendations.'
        : 'A scored match is not available for your target role yet. No recent catalog listings are available.',
      showPreferencesLink: false,
    }
  }
  return {
    summary:
      'No target role is set, so this is not a personalized match. The openings below are recent listings.',
    showPreferencesLink: true,
  }
}

export function readinessScoreLabel(input: {
  overallScoreReady?: boolean
  isHiringProbability?: boolean
  hasMinimumEvidence?: boolean
  score?: number | null
  hasTargetRole?: boolean
}): string {
  const show =
    input.overallScoreReady === true &&
    input.isHiringProbability !== true &&
    input.hasMinimumEvidence === true &&
    input.score != null &&
    input.hasTargetRole === true
  return show ? `${Math.round(input.score!)}%` : 'Not measured yet'
}

export function coverageLabel(covered: number, total: number): string {
  if (!(total > 0)) return 'Not measured'
  return `${covered} / ${total}`
}

const SPECIFIC_CONTINUATION =
  /^\/(?:learn\/courses\/[^/]+\/[^/]+\/[^/]+|practice\/sql\/[^/]+|practice\/dsa\/[^/]+|projects\/[^/]+|practice\/paths\/[^/]+|ai\/prompt-engineering\/challenges\/[^/]+)$/

/** Continue only when the link is a saved lesson, problem, project, or path. */
export function continuationAction(item: {
  href?: string | null
  progress_percent?: number | null
}): { label: 'Continue' | 'Start' | 'Explore'; note: string | null } {
  const href = (item.href ?? '').split('?')[0].replace(/\/$/, '')
  if (!href || href === '#') return { label: 'Explore', note: 'No saved place to resume.' }
  if (!SPECIFIC_CONTINUATION.test(href)) {
    return { label: 'Explore', note: 'This opens the track, not one saved lesson.' }
  }
  if ((item.progress_percent ?? 0) > 0) return { label: 'Continue', note: null }
  return { label: 'Start', note: null }
}

export type CatalogState = 'idle' | 'loading' | 'ready' | 'error'

export function catalogRouteKind(route: string | null | undefined): 'sql' | 'dsa' | null {
  if (!route) return null
  if (route === '/practice/sql' || route.startsWith('/practice/sql/')) return 'sql'
  if (route === '/practice/dsa' || route.startsWith('/practice/dsa/')) return 'dsa'
  return null
}

function countPhrase(count: number): string {
  return `${count} ${count === 1 ? 'item' : 'items'}`
}

/** A missing catalog total stays unknown. It is never shown as zero. */
export function practiceCountLabel(input: {
  itemCount: number | null | undefined
  externalRoute: string | null | undefined
  catalogCount: number | null | undefined
  catalogState: CatalogState
  availability?: string | null
}): string {
  const kind = catalogRouteKind(input.externalRoute)
  if (kind) {
    if (input.catalogState !== 'ready' || input.catalogCount == null) return 'Count unavailable'
    return countPhrase(input.catalogCount)
  }
  if (input.availability === 'coming_soon') return 'Not available yet'
  if (input.itemCount == null) return 'Count unavailable'
  return countPhrase(input.itemCount)
}

/** Next is a link only when the curriculum marks that lesson as open. */
export function nextLessonAction(input: {
  nextHref?: string | null
  blocks?: { module_slug: string; slug: string; status: string; title: string }[]
}): { kind: 'none' } | { kind: 'open'; href: string } | { kind: 'blocked'; title: string; reason: string } {
  const href = input.nextHref ?? ''
  if (!href || href === '#') return { kind: 'none' }
  const match = href.match(/\/learn\/courses\/[^/]+\/([^/]+)\/([^/]+)\/?$/)
  if (!match) return { kind: 'open', href }
  const block = (input.blocks ?? []).find((item) => item.module_slug === match[1] && item.slug === match[2])
  if (!block) return { kind: 'open', href }
  if (block.status === 'locked' || block.status === 'unavailable' || block.status === 'coming_soon') {
    return {
      kind: 'blocked',
      title: block.title,
      reason: `Complete the earlier lessons before opening ${block.title}.`,
    }
  }
  return { kind: 'open', href }
}

const SOLUTION_TYPES = new Set(['interactive_code', 'practice', 'worked_example'])

/** Reading lessons do not grow empty Solution or Hints tabs. */
export function lessonPanelTabs(
  lessonType: string | null | undefined,
  options: { hasHints: boolean; hasSolution: boolean },
): Array<'statement' | 'editor' | 'submissions' | 'solution' | 'hints' | 'help'> {
  const tabs: Array<'statement' | 'editor' | 'submissions' | 'solution' | 'hints' | 'help'> = ['statement']
  if (lessonType === 'interactive_code' || lessonType === 'practice') tabs.push('editor', 'submissions')
  if (SOLUTION_TYPES.has(lessonType ?? '') || options.hasSolution) tabs.push('solution')
  if (SOLUTION_TYPES.has(lessonType ?? '') || options.hasHints) tabs.push('hints')
  tabs.push('help')
  return tabs
}

export function pathIsOpen(input: {
  availability?: string | null
  externalRoute: string | null | undefined
  catalogCount: number | null | undefined
  catalogState: CatalogState
}): boolean {
  const kind = catalogRouteKind(input.externalRoute)
  if (kind && input.catalogState === 'ready' && (input.catalogCount ?? 0) > 0) return true
  return input.availability !== 'coming_soon'
}
