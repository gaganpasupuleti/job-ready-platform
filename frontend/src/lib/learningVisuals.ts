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

/** Repo-owned SVGs must be inert drawings. Active or external content fails the check. */
export function learningSvgIsStatic(source: string): boolean {
  const lowered = source.toLowerCase()
  if (lowered.includes('<script') || lowered.includes('foreignobject') || lowered.includes('<!entity') || lowered.includes('<!doctype')) {
    return false
  }
  if (/\son[a-z]+\s*=/.test(lowered)) return false
  if (lowered.includes('javascript:') || lowered.includes('data:')) return false
  if (/<(?:iframe|object|embed|audio|video|script|use|image|link|animate|set|handler|foreignobject)\b/.test(lowered)) {
    return false
  }
  const withoutSvgNamespace = source.replaceAll('xmlns="http://www.w3.org/2000/svg"', '')
  if (/https?:|\/\//.test(withoutSvgNamespace)) return false
  return true
}
