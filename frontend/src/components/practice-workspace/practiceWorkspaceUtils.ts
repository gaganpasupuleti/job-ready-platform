import { useEffect, type ReactNode } from 'react'

/** Non-component helpers for practice workspaces (kept separate for Fast Refresh). */

export function statusLabel(status?: string | null) {
  if (!status) return 'Not Started'
  const labels: Record<string, string> = {
    not_started: 'Not Started',
    unsolved: 'Not Started',
    attempted: 'Attempted',
    in_progress: 'In Progress',
    solved: 'Solved',
    completed: 'Completed',
    mastered: 'Mastered',
    locked: 'Locked',
  }
  return labels[status] ?? status.replace(/_/g, ' ')
}

export function apiErrorMessage(error: unknown, fallback = 'Request failed.') {
  if (error instanceof Error && error.message) return error.message
  return fallback
}

export function useWorkspaceShortcuts(handlers: {
  run?: () => void
  submit?: () => void
  enabled?: boolean
}) {
  useEffect(() => {
    if (handlers.enabled === false) return
    const onKey = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey) || event.key !== 'Enter') return
      const target = event.target as HTMLElement | null
      if (target && ['INPUT', 'SELECT'].includes(target.tagName) && target.tagName !== 'TEXTAREA') {
        return
      }
      event.preventDefault()
      if (event.shiftKey) handlers.submit?.()
      else handlers.run?.()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [handlers])
}

export type { ReactNode }
