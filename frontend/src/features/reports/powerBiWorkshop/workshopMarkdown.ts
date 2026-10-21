import type { WorkshopContent, WorkshopStep } from './types'

function stepMarkdown(step: WorkshopStep, index: number): string {
  const lines: string[] = []
  lines.push(`## ${index}. ${step.title}`)
  lines.push('')
  lines.push(`**Objective:** ${step.objective}`)
  lines.push('')
  if (step.prerequisites.length) {
    lines.push(`**Prerequisites:** ${step.prerequisites.join(', ')}`)
    lines.push('')
  }
  lines.push('### Actions')
  for (const action of step.actions) {
    lines.push(`1. ${action}`)
  }
  lines.push('')
  if (step.dax?.length) {
    lines.push('### DAX')
    for (const block of step.dax) {
      lines.push('```dax')
      lines.push(block.expression.trim())
      lines.push('```')
      lines.push('')
    }
  }
  if (step.visual) {
    lines.push(`### Visual (${step.visual.visualType})`)
    lines.push(`Fields: ${step.visual.fields.join(', ') || '—'}`)
    lines.push('')
  }
  if (step.expectedResult) {
    lines.push(`**Expected:** ${step.expectedResult}`)
    lines.push('')
  }
  if (step.verificationChecklist.length) {
    lines.push('**Checklist:**')
    for (const item of step.verificationChecklist) {
      lines.push(`- [ ] ${item}`)
    }
    lines.push('')
  }
  return lines.join('\n')
}

export function workshopToMarkdown(content: WorkshopContent): string {
  const lines: string[] = [
    `# ${content.title} — build guide`,
    '',
    `Content version: ${content.contentVersion}`,
    '',
    '## Learning outcomes',
    ...content.learningOutcomes.map((o) => `- ${o}`),
    '',
    '## Prerequisites',
    ...content.prerequisites.map((p) => `- ${p}`),
    '',
    `Tested Desktop: ${content.testedDesktopVersion}`,
    '',
  ]
  let n = 1
  for (const stage of content.stages.sort((a, b) => a.order - b.order)) {
    lines.push(`# Stage ${stage.order}: ${stage.title}`)
    lines.push('')
    lines.push(stage.summary)
    lines.push('')
    const stageSteps = content.steps.filter((s) => s.stageId === stage.id).sort((a, b) => a.order - b.order)
    for (const step of stageSteps) {
      lines.push(stepMarkdown(step, n))
      n += 1
    }
  }
  return lines.join('\n')
}
