/** Strip promo nodes and map former roadmap.sh URLs to in-app routes. */

const ROADMAP_SH_HOST = /^(?:www\.)?roadmap\.sh$/i

export function slugFromRoadmapShUrl(url: string): string | null {
  const trimmed = url.trim()
  if (!trimmed) return null
  try {
    const parsed = new URL(trimmed, 'https://roadmap.sh')
    if (!ROADMAP_SH_HOST.test(parsed.hostname)) return null
    const slug = parsed.pathname.replace(/^\//, '').split('/').filter(Boolean)[0]
    return slug && /^[a-z0-9-]+$/i.test(slug) ? slug.toLowerCase() : null
  } catch {
    return null
  }
}

export function internalRoadmapPath(
  url: string,
  allowedSlugs?: ReadonlySet<string>,
): string | null {
  const slug = slugFromRoadmapShUrl(url)
  if (!slug) return null
  if (allowedSlugs && !allowedSlugs.has(slug)) return null
  return `/roadmaps/${slug}`
}

export function shouldHideOfficialNode(
  raw: { type?: string; data?: { label?: string; href?: string; url?: string } },
): boolean {
  const label = (raw.data?.label ?? '').trim().toLowerCase()
  const href = (raw.data?.href ?? raw.data?.url ?? '').trim().toLowerCase()

  if (label === 'roadmap.sh') return true
  if (href === 'https://roadmap.sh' || href === 'http://roadmap.sh' || href === 'https://www.roadmap.sh') {
    return true
  }
  if (label.includes('find the detailed version of this roadmap')) return true

  return false
}

export function rewriteRoadmapShMarkdown(
  markdown: string,
  allowedSlugs?: ReadonlySet<string>,
): string {
  const withPaths = markdown.replace(
    /\]\(https?:\/\/(?:www\.)?roadmap\.sh\/([a-z0-9-]+)[^)]*\)/gi,
    (_match, slug: string) => {
      const normalized = slug.toLowerCase()
      if (allowedSlugs && !allowedSlugs.has(normalized)) {
        return `](https://roadmap.sh/${normalized})`
      }
      return `](/roadmaps/${normalized})`
    },
  )
  return withPaths.replace(/\]\(https?:\/\/(?:www\.)?roadmap\.sh\/?\)/gi, '](/roadmaps)')
}
