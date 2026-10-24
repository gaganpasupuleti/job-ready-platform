import type { RoadmapFixturePayload } from './types'

const BUNDLED_FAMILIES: Record<string, () => Promise<unknown>> = {
  'data-engineer': () => import('./fixtures/de-linked-draft.assembly.json'),
}

export async function loadRoadmapAssemblyFromBundle(
  familySlug: string,
  configVersion?: string,
): Promise<RoadmapFixturePayload | null> {
  const loader = BUNDLED_FAMILIES[familySlug]
  if (!loader) return null
  const mod = (await loader()) as { default: RoadmapFixturePayload }
  const payload = mod.default
  if (configVersion && payload.assembly.config_version !== configVersion) {
    return null
  }
  return payload
}
