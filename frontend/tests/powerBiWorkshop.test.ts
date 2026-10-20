import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, it } from 'node:test'

import { validateWorkshopContent } from '../src/features/reports/powerBiWorkshop/validateWorkshopContent.ts'
import type { WorkshopContent } from '../src/features/reports/powerBiWorkshop/types.ts'

const lab = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'reports', 'executive-sales-toast-lab')

describe('power bi workshop content', () => {
  it('validates executive sales toast curriculum', () => {
    const content = JSON.parse(readFileSync(join(lab, 'workshop-content.json'), 'utf8')) as WorkshopContent
    const issues = validateWorkshopContent(content)
    assert.deepEqual(issues, [])
    assert.ok(content.steps.length >= 40)
  })
})
