import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const catalogPath = join(root, 'public', 'official-roadmaps-index.json')
const catalog = JSON.parse(readFileSync(catalogPath, 'utf8'))
const rows = catalog.roadmaps ?? []

const slugRe = /^[a-z0-9-]+$/
let failures = 0

for (const row of rows) {
  if (!slugRe.test(row.family_slug)) {
    console.error('invalid slug', row.family_slug)
    failures += 1
  }
  if (!row.title?.trim()) {
    console.error('missing title', row.family_slug)
    failures += 1
  }
}

console.log(`catalog entries: ${rows.length}, failures: ${failures}`)
if (failures > 0) process.exit(1)
