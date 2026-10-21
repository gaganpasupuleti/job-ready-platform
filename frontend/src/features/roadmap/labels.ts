/** Plain-language labels — display only; no mastery/priority computation. */

import type { NodeAvailability, ResourceAvailability } from './types'

export function availabilityPlain(status: NodeAvailability): string {
  switch (status) {
    case 'available':
      return 'Available to start learning resources'
    case 'blocked_prerequisite':
      return 'Blocked — required prior work is not established'
    case 'resource_missing':
      return 'Learning resources are missing'
    case 'resource_inaccessible':
      return 'Resources exist but are unpublished or inaccessible'
    case 'execution_unavailable':
      return 'Execution is currently unavailable'
    case 'proof_policy_blocked':
      return 'Blocked by missing proof policy'
    case 'activity_completion_unspecified':
      return 'Completion rules are not configured'
    case 'config_incomplete':
      return 'Configuration is incomplete'
    default:
      return status
  }
}

export function resourceAvailabilityPlain(status: ResourceAvailability): string {
  switch (status) {
    case 'available':
      return 'Available'
    case 'missing':
      return 'Missing'
    case 'unpublished_or_inaccessible':
      return 'Unpublished or inaccessible'
    case 'execution_unavailable':
      return 'Execution unavailable'
    case 'not_applicable':
      return 'Not applicable'
    default:
      return status
  }
}

export function proofStatusPlain(status: string | null): string {
  if (!status) return 'Not provided'
  switch (status) {
    case 'not_evaluated':
      return 'Not evaluated (proof policy unset)'
    case 'no_applicable_evidence':
      return 'No applicable evidence'
    case 'needs_improvement':
      return 'Needs improvement under labeled policy'
    case 'meets_criterion':
      return 'Meets criterion under labeled policy'
    case 'incomplete_historical_coverage':
      return 'Incomplete historical coverage'
    default:
      return status.replaceAll('_', ' ')
  }
}

export function importancePlain(importance: string | null, isOptional: boolean): string {
  if (isOptional) return 'Optional'
  if (!importance) return 'Required'
  if (importance === 'core') return 'Required · core'
  if (importance === 'important') return 'Required · important'
  if (importance === 'nice_to_have') return 'Nice to have'
  return importance
}

export function phaseLabel(phaseKey: string | null): string {
  if (!phaseKey) return 'Ungrouped'
  return phaseKey
    .split('-')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

export function reasonCodePlain(code: string): string {
  return code.replaceAll('_', ' ')
}
