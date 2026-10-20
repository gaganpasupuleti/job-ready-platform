import type { WorkshopContent, WorkshopStep } from './types'

export type WorkshopValidationIssue = { path: string; message: string }

export function validateWorkshopContent(content: WorkshopContent): WorkshopValidationIssue[] {
  const issues: WorkshopValidationIssue[] = []
  const allStepIds = new Set(content.steps.map((s) => s.id))
  const stepIds = new Set<string>()
  const stageIds = new Set(content.stages.map((s) => s.id))

  for (const stage of content.stages) {
    if (!stage.id || !stage.title) {
      issues.push({ path: 'stages', message: 'Each stage needs id and title' })
    }
  }

  for (const step of content.steps) {
    if (stepIds.has(step.id)) {
      issues.push({ path: `steps.${step.id}`, message: 'Duplicate step id' })
    }
    stepIds.add(step.id)
    if (!stageIds.has(step.stageId)) {
      issues.push({ path: `steps.${step.id}`, message: `Unknown stageId ${step.stageId}` })
    }
    if (!step.title || !step.objective || step.actions.length === 0) {
      issues.push({ path: `steps.${step.id}`, message: 'Missing title, objective, or actions' })
    }
    for (const prereq of step.prerequisites) {
      if (!allStepIds.has(prereq)) {
        issues.push({ path: `steps.${step.id}`, message: `Unknown prerequisite ${prereq}` })
      }
    }
  }

  // Prerequisite order: prereq must appear before dependent in steps array
  const indexById = new Map(content.steps.map((s, i) => [s.id, i]))
  for (const step of content.steps) {
    const idx = indexById.get(step.id) ?? -1
    for (const prereq of step.prerequisites) {
      const pIdx = indexById.get(prereq)
      if (pIdx !== undefined && pIdx >= idx) {
        issues.push({
          path: `steps.${step.id}`,
          message: `Prerequisite ${prereq} must come before this step in the curriculum`,
        })
      }
    }
  }

  if (!content.contentVersion || !content.reportId) {
    issues.push({ path: 'meta', message: 'contentVersion and reportId are required' })
  }

  return issues
}

export function flattenStepsByStage(content: WorkshopContent): Map<string, WorkshopStep[]> {
  const map = new Map<string, WorkshopStep[]>()
  for (const stage of content.stages) {
    map.set(
      stage.id,
      content.steps.filter((s) => s.stageId === stage.id).sort((a, b) => a.order - b.order),
    )
  }
  return map
}
