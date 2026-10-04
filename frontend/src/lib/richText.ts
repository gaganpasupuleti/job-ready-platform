const SAFE_URL = /^(https?:\/\/|mailto:)/i

function stripControls(value: string): string {
  let out = ''
  for (const char of value) {
    const code = char.charCodeAt(0)
    if (code <= 31 || code === 127) continue
    out += char
  }
  return out
}

/** Drop raw HTML tokens. The renderer must not emit these. */
export function isDroppedMarkdownToken(type: string): boolean {
  return type === 'html' || type === 'space' || type === 'def'
}

/** Refuse javascript:, data:, and protocol-relative links. Relative paths and http(s)/mailto stay. */
export function safeHref(href: string | null | undefined): string | null {
  if (!href) return null
  const compact = stripControls(href).replace(/\s+/g, '')
  if (!compact || compact.startsWith('//')) return null
  let decoded = compact
  try {
    decoded = decodeURIComponent(compact)
  } catch {
    return null
  }
  const scheme = stripControls(decoded).replace(/\s+/g, '').toLowerCase()
  if (/^(javascript|data|vbscript|file|blob):/.test(scheme)) return null
  if (compact.startsWith('/') || compact.startsWith('#')) return compact
  return SAFE_URL.test(compact) ? compact : null
}

/** Keep single-line breaks readable without turning markdown lists into literal asterisks. */
export function prepareRichText(source: string): string {
  const normalized = source.replace(/\r\n/g, '\n').replace(/^\\([-*+]|\d+\.)/gm, '$1')
  const lines = normalized.split('\n')
  const out: string[] = []
  for (const line of lines) {
    const structural = /^\s*(?:[-*+]|\d+\.)\s+/.test(line) || /^\s*#{1,6}\s+/.test(line)
    if (structural || line.trim() === '') out.push(line)
    else out.push(line, '')
  }
  return out.join('\n')
}

function normalizeHeading(value: string | null | undefined): string {
  return (value ?? '').replace(/\s+/g, ' ').trim().toLowerCase()
}

/**
 * Page chrome owns the document title and any structured sections it already renders.
 * Only a leading heading that matches the page title is removed, plus a heading whose
 * text matches a chrome-owned section and the single block that follows it.
 */
export function omitChromeOwnedBlocks<T extends { type: string; text?: string }>(
  tokens: readonly T[],
  owned: { title?: string | null; headings?: string[] },
): T[] {
  const title = normalizeHeading(owned.title)
  const headings = new Set((owned.headings ?? []).map(normalizeHeading).filter(Boolean))
  const out: T[] = []
  let index = 0
  while (index < tokens.length && tokens[index].type === 'space') index += 1
  if (title && tokens[index]?.type === 'heading' && normalizeHeading(tokens[index].text) === title) {
    index += 1
    if (tokens[index]?.type === 'space') index += 1
  }
  while (index < tokens.length) {
    const token = tokens[index]
    if (token.type === 'heading' && headings.has(normalizeHeading(token.text))) {
      index += 1
      if (tokens[index]?.type === 'space') index += 1
      const next = tokens[index]
      if (next && (next.type === 'list' || next.type === 'paragraph')) index += 1
      if (tokens[index]?.type === 'space') index += 1
      continue
    }
    out.push(token)
    index += 1
  }
  return out
}
