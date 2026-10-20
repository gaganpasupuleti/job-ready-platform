import { useCallback, useMemo, useState } from 'react'

const STORAGE_PREFIX = 'jr:power-bi-lab:'

export function labProgressKey(reportId: string, contentVersion: string) {
  return `${STORAGE_PREFIX}${reportId}:${contentVersion}`
}

export function useLabProgress(reportId: string, contentVersion: string, stepIds: string[]) {
  const key = labProgressKey(reportId, contentVersion)
  const [completed, setCompleted] = useState<Set<string>>(() => readCompleted(key))

  const persist = useCallback(
    (next: Set<string>) => {
      setCompleted(next)
      try {
        localStorage.setItem(key, JSON.stringify([...next]))
      } catch {
        /* quota / private mode */
      }
    },
    [key],
  )

  const toggleComplete = useCallback(
    (stepId: string, done?: boolean) => {
      const next = new Set(completed)
      const should = done ?? !next.has(stepId)
      if (should) next.add(stepId)
      else next.delete(stepId)
      persist(next)
    },
    [completed, persist],
  )

  const resetProgress = useCallback(() => {
    persist(new Set())
  }, [persist])

  const percent = useMemo(() => {
    if (!stepIds.length) return 0
    const done = stepIds.filter((id) => completed.has(id)).length
    return Math.round((done / stepIds.length) * 100)
  }, [completed, stepIds])

  return { completed, toggleComplete, resetProgress, percent }
}

function readCompleted(key: string): Set<string> {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return new Set()
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return new Set()
    return new Set(parsed.filter((id): id is string => typeof id === 'string'))
  } catch {
    return new Set()
  }
}
