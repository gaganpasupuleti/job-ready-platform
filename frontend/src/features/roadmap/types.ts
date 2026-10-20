/** Roadmap assembly contract types (mirrors backend Phase 5 JSON). */

export type NodeAvailability =
  | 'available'
  | 'blocked_prerequisite'
  | 'resource_missing'
  | 'resource_inaccessible'
  | 'execution_unavailable'
  | 'proof_policy_blocked'
  | 'activity_completion_unspecified'
  | 'config_incomplete'

export type ResourceAvailability =
  | 'available'
  | 'missing'
  | 'unpublished_or_inaccessible'
  | 'execution_unavailable'
  | 'not_applicable'

export type EdgeRelation = 'prerequisite' | 'recommended_before' | 'next' | 'related'

export interface RoadmapResource {
  type: string
  ref: string
  availability: ResourceAvailability
  reason_codes: string[]
}

export interface RoadmapNode {
  node_key: string
  title: string
  phase_key: string | null
  sort_order: number
  skill_id: string | null
  skill_slug: string | null
  importance: string | null
  is_optional: boolean
  planned_index: number
  hard_prerequisite_node_keys: string[]
  unsatisfied_hard_prerequisite_node_keys: string[]
  availability: NodeAvailability
  availability_reason_codes: string[]
  proof_status: string | null
  readiness_status: string | null
  can_satisfy_as_prerequisite: boolean
  resources: RoadmapResource[]
}

export interface RoadmapEdge {
  from_node_key: string
  to_node_key: string
  relation_type: EdgeRelation | string
}

export interface RoadmapPhase {
  phase_key: string
  label: string
  node_keys: string[]
}

export interface RoadmapAssembly {
  family_slug: string
  config_version: string
  config_status: string
  config_curriculum_complete: boolean
  preview_only: boolean
  student_eligible: boolean
  algorithm_version: string
  gap_engine_version: string
  policy_version: string
  formula_version: string
  formula_label: string
  as_of: string
  phases: RoadmapPhase[]
  planned_sequence: string[]
  nodes: RoadmapNode[]
  edges: RoadmapEdge[]
  recommended_next_node_key: string | null
  recommended_next_reason_codes: string[]
  limitations: string[]
  missing_information: string[]
  experience_route_adaptation: string
}

export interface RoadmapFixtureMeta {
  source_backend_branch: string
  source_commit: string
  source_export_label?: string
  generated_at_source?: string
  warning?: string
  start_here?: {
    node_key: string | null
    reason_codes: string[]
    intended_start_node_key: string
  }
  seed_gaps?: string[]
}

export interface RoadmapFixturePayload {
  fixture_meta: RoadmapFixtureMeta
  assembly: RoadmapAssembly
}

export interface ResolvedDestination {
  href: string | null
  label: string
  kind: 'learn' | 'practice' | 'assessment' | 'project' | 'playground' | 'unresolved'
  note: string | null
  /** True when FE can open a known JobReady route for this ref. */
  resolvable: boolean
}
