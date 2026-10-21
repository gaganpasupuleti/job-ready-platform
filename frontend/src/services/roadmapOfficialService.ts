import axios from 'axios'

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

export class RoadmapGraphError extends Error {
  readonly status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'RoadmapGraphError'
    this.status = status
  }
}

export function normalizeOfficialGraph(data: OfficialRoadmapGraph, slug: string): OfficialRoadmapGraph {
  if (!data || !Array.isArray(data.nodes) || data.nodes.length === 0) {
    throw new RoadmapGraphError('Graph response was empty')
  }
  if (!Array.isArray(data.edges)) {
    throw new RoadmapGraphError('Graph response was missing edges')
  }
  for (const node of data.nodes) {
    if (!node?.id || !node.position) {
      throw new RoadmapGraphError('Graph response had invalid nodes')
    }
  }
  for (const edge of data.edges) {
    if (!edge?.id || !edge.source || !edge.target) {
      throw new RoadmapGraphError('Graph response had invalid edges')
    }
  }
  return { ...data, slug: data.slug ?? slug }
}

async function fetchGraphDevProxy(slug: string): Promise<OfficialRoadmapGraph> {
  const response = await fetch(`/roadmap-graph/${encodeURIComponent(slug)}.json`)
  if (!response.ok) {
    throw new RoadmapGraphError(`Graph unavailable (${response.status})`, response.status)
  }
  const data = (await response.json()) as OfficialRoadmapGraph
  return normalizeOfficialGraph(data, slug)
}

/** Production graphs are served by the API; dev may use the Vite proxy when the API is down. */
export async function fetchOfficialRoadmapGraph(slug: string): Promise<OfficialRoadmapGraph> {
  try {
    const { data } = await apiClient.get<OfficialRoadmapGraph>(apiEndpoints.roadmap.officialGraph(slug))
    return normalizeOfficialGraph(data, slug)
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status
      if (status === 401 || status === 403) {
        throw error
      }
      if (import.meta.env.DEV) {
        return fetchGraphDevProxy(slug)
      }
      throw new RoadmapGraphError(
        status === 404 ? 'This roadmap could not be found.' : 'Could not load roadmap graph.',
        status,
      )
    }
    if (import.meta.env.DEV) {
      return fetchGraphDevProxy(slug)
    }
    throw error
  }
}

export async function fetchOfficialTopic(
  slug: string,
  nodeId: string,
  oldId?: string,
): Promise<{ title: string; markdown: string; attribution?: string }> {
  const { data } = await apiClient.get<{ title: string; markdown: string; attribution?: string }>(
    apiEndpoints.roadmap.officialTopic(slug, nodeId),
    { params: oldId ? { old_id: oldId } : {} },
  )
  return data
}
