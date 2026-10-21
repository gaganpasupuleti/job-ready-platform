/**
 * Roadmap assembly loader (Phase 5 JSON contract).
 */

import { fetchRoadmapAssembly as fetchRoadmapAssemblyApi } from '@/services/roadmapService'

import type { RoadmapAssembly, RoadmapFixturePayload, RoadmapNode } from './types'

export class RoadmapLoadError extends Error {
  readonly code: 'not_dev' | 'fixture_unavailable' | 'invalid_contract' | 'api_unavailable'

  constructor(
    message: string,
    code: 'not_dev' | 'fixture_unavailable' | 'invalid_contract' | 'api_unavailable',
  ) {
    super(message)
    this.name = 'RoadmapLoadError'
    this.code = code
  }
}

function assertAssembly(raw: unknown): RoadmapAssembly {
  if (!raw || typeof raw !== 'object') {
    throw new RoadmapLoadError('Assembly payload missing', 'invalid_contract')
  }
  const a = raw as RoadmapAssembly
  if (!a.family_slug || !a.config_version || !Array.isArray(a.nodes) || !Array.isArray(a.edges)) {
    throw new RoadmapLoadError('Assembly contract fields incomplete', 'invalid_contract')
  }
  return a
}

function assertPayload(raw: unknown): RoadmapFixturePayload {
  if (!raw || typeof raw !== 'object') {
    throw new RoadmapLoadError('Roadmap payload missing', 'invalid_contract')
  }
  const payload = raw as RoadmapFixturePayload
  assertAssembly(payload.assembly)
  return payload
}

/** Load assembly for a role family (API, then bundled JSON for known drafts). */
export async function loadRoadmapAssembly(params: {
  familySlug: string
  configVersion?: string
}): Promise<RoadmapFixturePayload> {
  try {
    const payload = await fetchRoadmapAssemblyApi(params.familySlug, params.configVersion)
    return assertPayload(payload)
  } catch {
    throw new RoadmapLoadError('Could not load this roadmap.', 'api_unavailable')
  }
}

/**
 * Development-only fixture loader (offline / no API).
 */
export async function loadDevRoadmapFixture(): Promise<RoadmapFixturePayload> {
  if (!import.meta.env.DEV) {
    throw new RoadmapLoadError(
      'Roadmap draft fixtures are excluded from production builds.',
      'not_dev',
    )
  }
  const mod = await import('./fixtures/de-linked-draft.assembly.json')
  const payload = (mod.default ?? mod) as RoadmapFixturePayload
  assertAssembly(payload.assembly)
  return payload
}

export function configStorageKey(assembly: RoadmapAssembly): string {
  return `jr-roadmap-view:${assembly.family_slug}@${assembly.config_version}`
}

export function nodeByKey(assembly: RoadmapAssembly, key: string): RoadmapNode | undefined {
  return assembly.nodes.find((n) => n.node_key === key)
}

export function orderedPhases(assembly: RoadmapAssembly): RoadmapAssembly['phases'] {
  const firstIndex = new Map<string, number>()
  for (const n of assembly.nodes) {
    const pk = n.phase_key ?? 'ungrouped'
    const prev = firstIndex.get(pk)
    if (prev === undefined || n.planned_index < prev) firstIndex.set(pk, n.planned_index)
  }
  return [...assembly.phases].sort(
    (a, b) => (firstIndex.get(a.phase_key) ?? 999) - (firstIndex.get(b.phase_key) ?? 999),
  )
}
