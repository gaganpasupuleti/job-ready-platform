import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export interface OfficialRoadmapGraph {
  slug: string
  title?: { card?: string; page?: string }
  description?: string
  nodes: OfficialRoadmapNode[]
  edges: OfficialRoadmapEdge[]
  dimensions?: { width: number; height: number }
}

export interface OfficialRoadmapNode {
  id: string
  type?: string
  position?: { x: number; y: number }
  width?: number
  height?: number
  measured?: { width?: number; height?: number }
  data?: {
    label?: string
    oldId?: string
    href?: string
    color?: string
    backgroundColor?: string
    links?: Array<{ id?: string; label: string; href?: string; url?: string }>
    style?: Record<string, unknown>
  }
  style?: Record<string, unknown>
}

export interface OfficialRoadmapEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
  style?: Record<string, unknown>
}

async function fetchGraphFromRoadmapSh(slug: string): Promise<OfficialRoadmapGraph> {
  const response = await fetch(`/roadmap-graph/${encodeURIComponent(slug)}.json`)
  if (!response.ok) {
    throw new Error(`roadmap.sh returned ${response.status}`)
  }
  const data = (await response.json()) as OfficialRoadmapGraph
  if (!data?.nodes?.length) {
    throw new Error('Empty roadmap graph')
  }
  return { ...data, slug: data.slug ?? slug }
}

/** API when backend is up; dev proxy to roadmap.sh otherwise. */
export async function fetchOfficialRoadmapGraph(slug: string): Promise<OfficialRoadmapGraph> {
  try {
    const { data } = await apiClient.get<OfficialRoadmapGraph>(apiEndpoints.roadmap.officialGraph(slug))
    if (data?.nodes?.length) return data
  } catch {
    // Old or offline backend — load graph without it.
  }
  return fetchGraphFromRoadmapSh(slug)
}

export async function fetchOfficialTopic(
  slug: string,
  nodeId: string,
  oldId?: string,
): Promise<{ title: string; markdown: string }> {
  const { data } = await apiClient.get<{ title: string; markdown: string }>(
    apiEndpoints.roadmap.officialTopic(slug, nodeId),
    { params: oldId ? { old_id: oldId } : {} },
  )
  return data
}
