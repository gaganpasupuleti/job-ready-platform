import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createHash } from 'node:crypto'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const lab = join(root, 'public', 'reports', 'executive-sales-toast-lab')

const workshop = JSON.parse(readFileSync(join(lab, 'workshop-content.json'), 'utf8'))
const manifest = JSON.parse(readFileSync(join(lab, 'manifest.json'), 'utf8'))

const stepIds = new Set()
for (const step of workshop.steps) {
  assert.ok(step.id && step.stageId, `step missing ids: ${step.title}`)
  assert.equal(stepIds.has(step.id), false, `duplicate step ${step.id}`)
  stepIds.add(step.id)
  for (const img of step.images ?? []) {
    const path = join(lab, img.src)
    assert.ok(existsSync(path), `missing image ${img.src} for step ${step.id}`)
  }
}

for (const step of workshop.steps) {
  for (const prereq of step.prerequisites ?? []) {
    assert.ok(stepIds.has(prereq), `${step.id} unknown prereq ${prereq}`)
  }
}

assert.ok(manifest.visualCount > 0, 'manifest visualCount must be > 0')
assert.ok(manifest.sourcePbixSha256, 'manifest missing sourcePbixSha256')

const zipPath = join(lab, 'datasets.zip')
assert.ok(existsSync(zipPath), 'datasets.zip missing')
const zipBuf = readFileSync(zipPath)
assert.ok(zipBuf.length > 1000, 'datasets.zip too small')

const expected = JSON.parse(readFileSync(join(lab, 'expected-results.json'), 'utf8'))
const display = expected.displayCurrency ?? expected.unfiltered
assert.ok(display['Total Sales'] > 0, 'expected-results missing Total Sales')
const sales = display['Total Sales']
const cost = display['Total Cost']
const profit = display['Total Profit']
assert.ok(Math.abs(sales - cost - profit) < 0.011, `KPIs do not reconcile: ${sales} - ${cost} !== ${profit}`)
assert.equal(expected.reconciliation?.matchesDisplayProfit, true, 'reconciliation flag must be true')

console.log(`Power BI lab validation OK (${workshop.steps.length} steps, manifest v${manifest.extractorVersion})`)
