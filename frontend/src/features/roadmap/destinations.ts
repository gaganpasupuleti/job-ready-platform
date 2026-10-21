/**
 * Resolve roadmap resource refs to JobReady frontend routes.
 * Does not invent URLs. Coding deep-links require UUID (not slug).
 */

import type { ResolvedDestination, RoadmapNode, RoadmapResource } from './types'

/**
 * Fixture-local lesson path for the known export lesson only.
 * General course_lesson resolution still needs module slug from API.
 */
const FIXTURE_LESSON_PATHS: Record<string, string> = {
  'what-is-python': '/learn/courses/python-foundations/getting-started/what-is-python',
}

export function resolveResourceDestination(
  resource: RoadmapResource,
  _node?: RoadmapNode,
): ResolvedDestination {
  const type = resource.type.toLowerCase()
  const ref = resource.ref

  if (type === 'learning_material' || type === 'material') {
    return {
      href: `/learn/materials/${encodeURIComponent(ref)}`,
      label: 'Open learning material',
      kind: 'learn',
      note: null,
      resolvable: true,
    }
  }

  if (type === 'course') {
    return {
      href: `/learn/courses/${encodeURIComponent(ref)}`,
      label: 'Open course',
      kind: 'learn',
      note: null,
      resolvable: true,
    }
  }

  if (type === 'course_lesson' || type === 'lesson') {
    const known = FIXTURE_LESSON_PATHS[ref]
    if (known) {
      return {
        href: known,
        label: 'Open course lesson',
        kind: 'learn',
        note: 'Lesson path uses fixture-local module mapping (module slug not in assembly export).',
        resolvable: true,
      }
    }
    return {
      href: null,
      label: 'Course lesson',
      kind: 'unresolved',
      note: `Cannot resolve lesson "${ref}" without course + module slugs from the API.`,
      resolvable: false,
    }
  }

  if (type === 'sql_problem') {
    return {
      href: `/practice/sql/${encodeURIComponent(ref)}`,
      label: 'Open SQL practice problem',
      kind: 'practice',
      note: 'Assessed SQL Practice — not the SQL Playground.',
      resolvable: true,
    }
  }

  if (type === 'coding_problem') {
    // Routes are /practice/dsa/:problemId (UUID). Slug alone cannot deep-link safely.
    return {
      href: null,
      label: 'Coding problem',
      kind: 'unresolved',
      note:
        resource.availability === 'execution_unavailable'
          ? `Coding Run/Submit locked (${resource.reason_codes.join(', ') || 'execution_unavailable'}). Deep link needs problem UUID, not slug "${ref}".`
          : `Coding workspace URLs use problem UUID; slug "${ref}" cannot be resolved without the coding API.`,
      resolvable: false,
    }
  }

  if (type === 'project') {
    return {
      href: `/projects/${encodeURIComponent(ref)}`,
      label: 'Open project',
      kind: 'project',
      note: null,
      resolvable: true,
    }
  }

  return {
    href: null,
    label: type,
    kind: 'unresolved',
    note: `Unsupported or unknown resource type "${type}" for ref "${ref}".`,
    resolvable: false,
  }
}

export function resourceActionLabel(type: string): string {
  switch (type.toLowerCase()) {
    case 'learning_material':
    case 'material':
      return 'Learn'
    case 'course':
    case 'course_lesson':
    case 'lesson':
      return 'Learn'
    case 'sql_problem':
      return 'Practice (SQL)'
    case 'coding_problem':
      return 'Practice (Coding)'
    case 'project':
      return 'Project'
    default:
      return 'Resource'
  }
}
