import axios from 'axios'

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
  graph_available?: boolean
  articles_available?: boolean
}

export interface RoadmapCatalogResponse {
  roadmaps: RoadmapCatalogItem[]
  source: 'api' | 'bundle'
  meta?: {
    total?: number
    with_articles?: number
    with_graph_cache?: number
    has_bundled_catalog?: boolean
  }
}

function isUsableApiCatalog(data: {
  roadmaps?: RoadmapCatalogItem[]
  source?: string
  meta?: RoadmapCatalogResponse['meta']
}): boolean {
  const rows = data.roadmaps ?? []
  if (data.source === 'official' && data.meta?.has_bundled_catalog && rows.length > 0) {
    return true
  }
  if (data.source === 'legacy' && rows.length <= 1) return false
  const onlyDraft =
    rows.length === 1 && rows[0]?.family_slug === 'data-engineer' && rows[0]?.preview_only
  return rows.length > 0 && !onlyDraft
}

async function loadBundledCatalog(): Promise<RoadmapCatalogResponse> {
  try {
    const response = await fetch('/official-roadmaps-index.json', { cache: 'no-cache' })
    if (response.ok) {
      const data = (await response.json()) as { roadmaps: RoadmapCatalogItem[] }
      if (data.roadmaps?.length) {
        return {
          roadmaps: data.roadmaps.map((row) => ({
            ...row,
            graph_available: row.graph_available ?? false,
            articles_available: row.articles_available ?? false,
          })),
          source: 'bundle',
          meta: { total: data.roadmaps.length, has_bundled_catalog: true },
        }
      }
    }
  } catch {
    // ignore
  }
  return { roadmaps: [], source: 'bundle', meta: { total: 0 } }
}

export async function fetchRoadmapCatalog(): Promise<RoadmapCatalogResponse> {
  try {
    const { data } = await apiClient.get<{
      roadmaps: RoadmapCatalogItem[]
      source?: string
      meta?: RoadmapCatalogResponse['meta']
    }>(apiEndpoints.roadmap.catalog)

    if (isUsableApiCatalog(data)) {
      return { roadmaps: data.roadmaps, source: 'api', meta: data.meta }
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status
      if (status === 401 || status === 403) {
        throw error
      }
    }
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
