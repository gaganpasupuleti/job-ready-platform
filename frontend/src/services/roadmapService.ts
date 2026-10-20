import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type { RoadmapFixturePayload } from '@/features/roadmap/types'

export interface RoadmapCatalogItem {
  family_slug: string
  title: string
  config_version?: string
  description: string
  preview_only: boolean
  student_eligible: boolean
  source?: string
}

export interface RoadmapCatalogResponse {
  roadmaps: RoadmapCatalogItem[]
  source: 'api' | 'bundle'
}

async function loadBundledCatalog(): Promise<RoadmapCatalogResponse> {
  try {
    const response = await fetch('/official-roadmaps-index.json', { cache: 'no-cache' })
    if (response.ok) {
      const data = (await response.json()) as { roadmaps: RoadmapCatalogItem[] }
      if (data.roadmaps?.length) {
        return { roadmaps: data.roadmaps, source: 'bundle' }
      }
    }
  } catch {
    // ignore
  }
  return {
    roadmaps: [
      {
        family_slug: 'python',
        title: 'Python',
        description: 'Interactive Python developer career path.',
        preview_only: false,
        student_eligible: true,
        source: 'official',
      },
    ],
    source: 'bundle',
  }
}

export async function fetchRoadmapCatalog(): Promise<RoadmapCatalogResponse> {
  try {
    const { data } = await apiClient.get<{ roadmaps: RoadmapCatalogItem[]; source?: string }>(
      apiEndpoints.roadmap.catalog,
    )
    if (data.roadmaps?.length) {
      return { roadmaps: data.roadmaps, source: 'api' }
    }
  } catch {
    // Backend old or offline.
  }
  return loadBundledCatalog()
}

export async function fetchRoadmapAssembly(
  familySlug: string,
  configVersion?: string,
): Promise<RoadmapFixturePayload> {
  const { data } = await apiClient.get<RoadmapFixturePayload>(apiEndpoints.roadmap.assembly, {
    params: {
      family_slug: familySlug,
      ...(configVersion ? { config_version: configVersion } : {}),
    },
  })
  return data
}
