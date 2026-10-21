import { readFileSync, writeFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

import { workshopToMarkdown } from '../src/features/reports/powerBiWorkshop/workshopMarkdown.ts'

const lab = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'reports', 'executive-sales-toast-lab')
const content = JSON.parse(readFileSync(join(lab, 'workshop-content.json'), 'utf8'))
writeFileSync(join(lab, 'build-guide.md'), workshopToMarkdown(content), 'utf8')
console.log('Wrote build-guide.md')
