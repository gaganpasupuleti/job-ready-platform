import DOMPurify from 'dompurify'

const ALLOWED_URI_REGEXP = /^(?:(?:https?|mailto|tel):|\/|#)/i

export function sanitizeArticleHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_URI_REGEXP,
    ADD_ATTR: ['target', 'rel'],
  })
}
