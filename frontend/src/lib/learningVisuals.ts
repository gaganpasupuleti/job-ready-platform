/**
 * Approved lesson diagrams are same-origin static files.
 * Markdown image paths are untrusted. Anything else stays alt text.
 *
 * Later phases should keep this allowlist. Question images, explanation
 * images, and interactive algorithm steps need their own reviewed batches.
 * They should store a path, not HTML, and they should not add columns until
 * that batch exists. Step controls belong in a later client component whose
 * steps are repo-owned data, not scripts from Markdown.
 */
const APPROVED_LEARNING_IMAGE =
  /^\/learning-visuals\/(?:crt|dsa|mcq|interviews)\/[a-z0-9]+(?:-[a-z0-9]+)*\.(?:svg|png|webp)$/

function stripControls(value: string): string {
  let out = ''
  for (const char of value) {
    const code = char.charCodeAt(0)
    if (code <= 31 || code === 127) continue
    out += char
  }
  return out
}

/** Return a same-origin learning-visual path, or null when the URL is not approved. */
export function approvedLearningImageSrc(href: string | null | undefined): string | null {
  if (!href) return null
  const compact = stripControls(href).replace(/\s+/g, '')
  if (!compact || !compact.startsWith('/') || compact.startsWith('//')) return null
  if (compact.includes('\\') || compact.includes('?') || compact.includes('#')) return null
  let decoded = compact
  try {
    decoded = decodeURIComponent(compact)
  } catch {
    return null
  }
  decoded = stripControls(decoded).replace(/\s+/g, '')
  if (!decoded || decoded.includes('%') || decoded.includes('..')) return null
  if (decoded.includes('\\') || decoded.includes('?') || decoded.includes('#') || decoded.includes('//')) return null
  if (/^(?:javascript|data|vbscript|file|blob|https?):/i.test(decoded)) return null
  if (!APPROVED_LEARNING_IMAGE.test(decoded)) return null
  return decoded
}

const SVG_ELEMENTS = new Set([
  'svg',
  'title',
  'desc',
  'g',
  'rect',
  'circle',
  'ellipse',
  'line',
  'polyline',
  'polygon',
  'path',
  'text',
  'tspan',
])

const SVG_ATTRIBUTES = new Set([
  'xmlns',
  'viewbox',
  'width',
  'height',
  'x',
  'y',
  'x1',
  'y1',
  'x2',
  'y2',
  'dx',
  'dy',
  'cx',
  'cy',
  'r',
  'rx',
  'ry',
  'points',
  'd',
  'fill',
  'stroke',
  'stroke-width',
  'stroke-linecap',
  'stroke-linejoin',
  'stroke-miterlimit',
  'font-family',
  'font-size',
  'font-weight',
  'text-anchor',
  'opacity',
  'fill-opacity',
  'stroke-opacity',
  'transform',
  'id',
])

const SVG_NAMESPACE = 'http://www.w3.org/2000/svg'
const UNSAFE_SVG_VALUE = /url\s*\(|javascript:|data:|https?:|\/\/|expression\s*\(|<|>|@import/i

export type LessonParagraphToken = { type: string; href?: string | null; text?: string }

export type LessonParagraphSegment<T extends LessonParagraphToken> =
  | { kind: 'inline'; tokens: T[] }
  | { kind: 'diagram'; token: T }

function decodedMarkdownText(value: string): string {
  return value
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&')
}

/**
 * Split a Markdown paragraph so an approved diagram is not nested inside a `<p>`.
 * Unsafe image tokens stay with the surrounding text and render as alt text.
 */
export function splitLessonParagraph<T extends LessonParagraphToken>(tokens: readonly T[]): LessonParagraphSegment<T>[] {
  const segments: LessonParagraphSegment<T>[] = []
  let inlineTokens: T[] = []
  const flush = () => {
    const meaningful = inlineTokens.some((token) => token.type !== 'text' || decodedMarkdownText(token.text ?? '').trim() !== '')
    if (meaningful) segments.push({ kind: 'inline', tokens: inlineTokens })
    inlineTokens = []
  }
  for (const token of tokens) {
    if (token.type === 'image' && approvedLearningImageSrc(token.href)) {
      flush()
      segments.push({ kind: 'diagram', token })
      continue
    }
    inlineTokens.push(token)
  }
  flush()
  return segments
}

function svgAttributeValueIsSafe(name: string, value: string): boolean {
  if (name === 'xmlns') return value === SVG_NAMESPACE
  if (UNSAFE_SVG_VALUE.test(value)) return false
  if (name === 'id') return /^[A-Za-z][A-Za-z0-9_-]*$/.test(value)
  if (name === 'fill' || name === 'stroke') return value === 'none' || value === 'currentColor' || /^#[0-9a-fA-F]{3,8}$/.test(value)
  if (name === 'font-family') return /^[A-Za-z0-9 ,'-]+$/.test(value)
  if (name === 'font-weight') return /^(?:normal|bold|[1-9]00)$/.test(value)
  if (name === 'text-anchor') return /^(?:start|middle|end)$/.test(value)
  if (name === 'stroke-linecap') return /^(?:butt|round|square)$/.test(value)
  if (name === 'stroke-linejoin') return /^(?:miter|round|bevel)$/.test(value)
  if (name === 'viewbox' || name === 'points') return /^[\d.\s,-]+$/.test(value) && !value.includes('--')
  if (name === 'd') return /^[MmLlHhVvCcSsQqTtAaZz0-9eE.,\s+-]+$/.test(value)
  if (name === 'transform') return /^(?:translate|rotate|scale|skewX|skewY)\([\d.\s,-]+\)(?:\s+(?:translate|rotate|scale|skewX|skewY)\([\d.\s,-]+\))*$/.test(value)
  return /^-?\d*\.?\d+(?:px|em|%)?$/.test(value)
}

/** Repo-owned SVGs must be inert drawings. Anything outside the element and attribute allowlist fails. */
export function learningSvgIsStatic(source: string): boolean {
  const trimmed = source.trim()
  if (!trimmed.startsWith('<svg') || !trimmed.endsWith('</svg>')) return false
  if (/<!--|<!|<\?|<!\[CDATA\[/.test(trimmed)) return false
  const tags = trimmed.match(/<\/?[a-zA-Z][^<>]*>/g)
  if (!tags) return false
  let svgOpens = 0
  for (const tag of tags) {
    const parsed = /^<(\/?)([a-zA-Z][\w:-]*)([^<>]*?)>$/.exec(tag)
    if (!parsed) return false
    const closing = parsed[1] === '/'
    const element = parsed[2].toLowerCase()
    if (!SVG_ELEMENTS.has(element)) return false
    if (element === 'svg') svgOpens += closing ? -1 : 1
    if (svgOpens > 1 || svgOpens < 0) return false
    if (closing) {
      if (parsed[3].trim() !== '') return false
      continue
    }
    const attrs = parsed[3].trim().replace(/\/$/, '').trim()
    if (!attrs) continue
    const attrPattern = /([^\s=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|(\S+)))?/g
    let consumed = ''
    for (const attr of attrs.matchAll(attrPattern)) {
      consumed += attr[0]
      const name = attr[1].toLowerCase()
      if (name.startsWith('on') || name.includes(':') || name === 'style' || name === 'href' || name === 'src') return false
      if (!SVG_ATTRIBUTES.has(name)) return false
      if (attr[4] !== undefined || (attr[2] === undefined && attr[3] === undefined)) return false
      const value = attr[2] ?? attr[3] ?? ''
      if (!svgAttributeValueIsSafe(name, value)) return false
    }
    if (consumed.replace(/\s+/g, '') !== attrs.replace(/\s+/g, '')) return false
  }
  if (svgOpens !== 0) return false
  const withoutTags = trimmed.replace(/<\/?[a-zA-Z][^<>]*>/g, '')
  if (withoutTags.includes('<') || withoutTags.includes('>')) return false
  return true
}
