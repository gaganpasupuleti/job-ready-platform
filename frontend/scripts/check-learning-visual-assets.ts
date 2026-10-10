/**
 * Check the six Phase 1 diagrams.
 *
 * Local files are always checked. Set ASSET_BASE_URL to the deployed frontend
 * origin to require HTTP 200 and an SVG body for each public path.
 *
 *   node --experimental-strip-types scripts/check-learning-visual-assets.ts
 *   ASSET_BASE_URL=https://frontend-production-f65c0.up.railway.app node --experimental-strip-types scripts/check-learning-visual-assets.ts
 */
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

import { learningSvgIsStatic } from '../src/lib/learningVisuals.ts'

export const PHASE1_ASSETS = [
  '/learning-visuals/crt/percentages-quarter.svg',
  '/learning-visuals/crt/number-pattern.svg',
  '/learning-visuals/crt/verbal-claim.svg',
  '/learning-visuals/crt/data-interpretation.svg',
  '/learning-visuals/dsa/complexity-growth.svg',
  '/learning-visuals/dsa/array-reversal.svg',
]

export function localAssetFailures(root = path.resolve('public')): string[] {
  const failures: string[] = []
  for (const asset of PHASE1_ASSETS) {
    const file = path.join(root, asset.replace(/^\//, ''))
    if (!fs.existsSync(file)) {
      failures.push(`missing ${asset}`)
      continue
    }
    const source = fs.readFileSync(file, 'utf8')
    if (!learningSvgIsStatic(source)) failures.push(`unsafe ${asset}`)
  }
  return failures
}

export async function remoteAssetFailures(baseUrl: string): Promise<string[]> {
  const failures: string[] = []
  const origin = baseUrl.replace(/\/$/, '')
  for (const asset of PHASE1_ASSETS) {
    const response = await fetch(`${origin}${asset}`)
    if (response.status !== 200) {
      failures.push(`${asset} HTTP ${response.status}`)
      continue
    }
    const type = response.headers.get('content-type') ?? ''
    if (!type.includes('image/svg')) failures.push(`${asset} content-type ${type || 'missing'}`)
    const body = await response.text()
    if (!learningSvgIsStatic(body)) failures.push(`${asset} failed the static SVG check`)
  }
  return failures
}

const isDirectRun = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href
if (isDirectRun) {
  const local = localAssetFailures()
  const baseUrl = process.env.ASSET_BASE_URL
  const remote = baseUrl ? await remoteAssetFailures(baseUrl) : []
  const failures = [...local, ...remote]
  if (failures.length) {
    console.error(failures.join('\n'))
    process.exit(1)
  }
  console.log(JSON.stringify({ assets: PHASE1_ASSETS.length, baseUrl: baseUrl ?? null, ok: true }))
}
