import type { Mode } from './content'
export interface TypingResult {
  id: string
  date: string
  mode: Mode
  label: string
  seconds: number
  wpm: number
  accuracy: number
  errors: number
  elapsedMs: number
}
const key = (userId: string) => `jr:typing:v1:${userId}`
function valid(value: unknown): value is TypingResult {
  if (!value || typeof value !== 'object') return false
  const r = value as TypingResult
  return (
    typeof r.id === 'string' &&
    typeof r.date === 'string' &&
    Number.isFinite(Date.parse(r.date)) &&
    ['text', 'code', 'custom'].includes(r.mode) &&
    typeof r.label === 'string' &&
    r.label.length < 150 &&
    [r.seconds, r.wpm, r.accuracy, r.errors, r.elapsedMs].every(
      (n) => Number.isFinite(n) && n >= 0,
    ) &&
    r.accuracy <= 100
  )
}
export function readHistory(userId: string): TypingResult[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(key(userId)) ?? '[]')
    return Array.isArray(value) ? value.filter(valid).slice(0, 50) : []
  } catch {
    return []
  }
}
export function saveResult(userId: string, result: TypingResult): boolean {
  try {
    const history = readHistory(userId)
    localStorage.setItem(
      key(userId),
      JSON.stringify([result, ...history.filter((r) => r.id !== result.id)].slice(0, 50)),
    )
    return true
  } catch {
    return false
  }
}
export function clearHistory(userId: string): boolean {
  try {
    localStorage.removeItem(key(userId))
    return true
  } catch {
    return false
  }
}
