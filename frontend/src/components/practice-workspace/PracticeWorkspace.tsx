import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from 'react'
import { Link } from 'react-router-dom'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { statusLabel } from '@/components/practice-workspace/practiceWorkspaceUtils'
import { cn } from '@/utils/cn'

export type PracticeStatus =
  | 'not_started'
  | 'unsolved'
  | 'attempted'
  | 'in_progress'
  | 'solved'
  | 'completed'
  | 'mastered'
  | 'locked'
  | string

export function PracticeStatusBadge({ status }: { status?: string | null }) {
  const key = status || 'not_started'
  const variant =
    key === 'solved' || key === 'completed' || key === 'mastered'
      ? 'success'
      : key === 'locked'
        ? 'warning'
        : key === 'attempted' || key === 'in_progress'
          ? 'accent'
          : 'default'
  return <Badge variant={variant}>{statusLabel(key)}</Badge>
}

export function LoadingState({ label = 'Loading workspace' }: { label?: string }) {
  return (
    <div className="animate-pulse space-y-3" role="status" aria-label={label}>
      <div className="h-8 w-1/3 rounded bg-[var(--color-surface-muted)]" />
      <div className="h-40 rounded bg-[var(--color-surface-muted)]" />
      <div className="h-24 rounded bg-[var(--color-surface-muted)]" />
    </div>
  )
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="rounded-md border border-dashed border-[var(--color-border)] p-6 text-sm">
      <p className="font-medium text-[var(--color-text)]">{title}</p>
      {description && <p className="mt-1 text-[var(--color-text-muted)]">{description}</p>}
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
      {message}
    </div>
  )
}

export function SuccessState({
  title,
  children,
}: {
  title: string
  children?: ReactNode
}) {
  return (
    <div className="rounded-md border border-emerald-300 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950">
      <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">{title}</p>
      {children && <div className="mt-2 text-sm text-[var(--color-text)]">{children}</div>}
    </div>
  )
}

export function PracticeProgress({
  percent,
  label,
}: {
  percent: number
  label?: string
}) {
  const value = Math.max(0, Math.min(100, percent))
  return (
    <div className="min-w-[140px]">
      {label && <p className="mb-1 text-xs text-[var(--color-text-muted)]">{label}</p>}
      <div
        className="h-2 overflow-hidden rounded-full bg-[var(--color-surface-muted)]"
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="h-full rounded-full bg-[var(--color-accent)]" style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

export function PracticeHeader({
  backTo,
  backLabel,
  title,
  children,
}: {
  backTo: string
  backLabel: string
  title: string
  children?: ReactNode
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <Link to={backTo} className="text-xs text-[var(--color-accent)] hover:underline">
          ← {backLabel}
        </Link>
        <h1 className="mt-1 text-lg font-semibold text-[var(--color-text)]">{title}</h1>
        {children}
      </div>
    </div>
  )
}

export function PracticeTabs({
  tabs,
  value,
  onChange,
}: {
  tabs: Array<{ id: string; label: string }>
  value: string
  onChange: (id: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-1 border-b border-[var(--color-border)]" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={value === tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            'rounded-t-md px-3 py-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)]',
            value === tab.id
              ? 'border-b-2 border-[var(--color-accent)] text-[var(--color-accent)]'
              : 'text-[var(--color-text-muted)]',
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

export interface NavItem {
  id: string
  slug?: string
  title: string
  status?: string | null
  href: string
}

export function ProblemNavigator({
  items,
  currentId,
}: {
  items: NavItem[]
  currentId?: string
}) {
  if (!items.length) return null
  return (
    <nav aria-label="Problem list" className="max-h-48 overflow-auto rounded-md border border-[var(--color-border)] p-2">
      <ul className="space-y-1 text-xs">
        {items.map((item) => {
          const solved = item.status === 'solved' || item.status === 'completed' || item.status === 'mastered'
          const current = item.id === currentId
          const mark = solved ? '✓' : current ? '●' : '○'
          return (
            <li key={item.id}>
              <Link
                to={item.href}
                className={cn(
                  'flex items-center gap-2 rounded px-1 py-0.5 hover:bg-[var(--color-surface-muted)]',
                  current && 'font-medium text-[var(--color-accent)]',
                )}
              >
                <span aria-hidden>{mark}</span>
                <span className="truncate">{item.title}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

export function NextItemCard({
  href,
  title,
  disabled,
}: {
  href?: string | null
  title: string
  disabled?: boolean
}) {
  if (!href || disabled) {
    return <p className="text-sm text-[var(--color-text-muted)]">No next item.</p>
  }
  return (
    <Link
      to={href}
      className="block rounded-md border border-[var(--color-border)] p-3 text-sm hover:border-[var(--color-accent)]"
    >
      Next: {title}
    </Link>
  )
}

export function HintPanel({
  hints,
  revealed,
  onReveal,
  empty = 'No hints for this item.',
}: {
  hints: string[]
  revealed: number
  onReveal: () => void
  empty?: string
}) {
  if (!hints.length) return <EmptyState title={empty} />
  return (
    <div className="space-y-3">
      {hints.slice(0, revealed).map((hint, index) => (
        <div key={index} className="rounded-md border border-[var(--color-border)] p-3 text-sm">
          <p className="mb-1 text-xs text-[var(--color-text-subtle)]">Hint {index + 1}</p>
          <p>{hint}</p>
        </div>
      ))}
      {revealed < hints.length && (
        <Button type="button" variant="secondary" size="sm" onClick={onReveal}>
          Reveal Hint {revealed + 1}
        </Button>
      )}
    </div>
  )
}

function useIsDesktopLayout(minWidth = 1024) {
  return useSyncExternalStore(
    (onStoreChange) => {
      if (typeof window === 'undefined') return () => undefined
      const mq = window.matchMedia(`(min-width: ${minWidth}px)`)
      mq.addEventListener('change', onStoreChange)
      return () => mq.removeEventListener('change', onStoreChange)
    },
    () => (typeof window !== 'undefined' ? window.matchMedia(`(min-width: ${minWidth}px)`).matches : true),
    () => true,
  )
}

export function WorkspaceSplit({
  storageKey,
  left,
  right,
  bottom,
  mobileTab,
  onMobileTab,
}: {
  storageKey: string
  left: ReactNode
  right: ReactNode
  bottom?: ReactNode
  mobileTab: 'problem' | 'code' | 'output'
  onMobileTab: (tab: 'problem' | 'code' | 'output') => void
}) {
  const isDesktop = useIsDesktopLayout()
  const [leftPct, setLeftPct] = useState(() => {
    const stored = Number(localStorage.getItem(storageKey) || 42)
    return Number.isFinite(stored) ? Math.min(70, Math.max(22, stored)) : 42
  })
  const [bottomPct, setBottomPct] = useState(() => {
    const stored = Number(localStorage.getItem(`${storageKey}:bottom`) || 28)
    return Number.isFinite(stored) ? Math.min(55, Math.max(16, stored)) : 28
  })
  const dragging = useRef<'x' | 'y' | null>(null)
  const rootRef = useRef<HTMLDivElement>(null)

  const onPointerMove = useCallback((event: PointerEvent) => {
    const root = rootRef.current
    if (!root || !dragging.current) return
    const rect = root.getBoundingClientRect()
    if (dragging.current === 'x') {
      const next = ((event.clientX - rect.left) / rect.width) * 100
      setLeftPct(Math.min(70, Math.max(22, next)))
    } else {
      const next = ((rect.bottom - event.clientY) / rect.height) * 100
      setBottomPct(Math.min(55, Math.max(16, next)))
    }
  }, [])

  const stopDrag = useCallback(() => {
    dragging.current = null
    document.body.style.cursor = ''
    localStorage.setItem(storageKey, String(leftPct))
    localStorage.setItem(`${storageKey}:bottom`, String(bottomPct))
  }, [bottomPct, leftPct, storageKey])

  useEffect(() => {
    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', stopDrag)
    return () => {
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerup', stopDrag)
    }
  }, [onPointerMove, stopDrag])

  // Render only one layout tree so Playwright/a11y do not see duplicate hidden panels.
  if (!isDesktop) {
    return (
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div className="mb-2 flex gap-1" role="tablist" aria-label="Workspace">
          {(['problem', 'code', 'output'] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              className={cn(
                'flex-1 rounded-md border px-2 py-1.5 text-sm capitalize',
                mobileTab === tab
                  ? 'border-[var(--color-accent)] text-[var(--color-accent)]'
                  : 'border-[var(--color-border)] text-[var(--color-text-muted)]',
              )}
              onClick={() => onMobileTab(tab)}
            >
              {tab === 'code' ? 'Code' : tab === 'output' ? 'Output' : 'Problem'}
            </button>
          ))}
        </div>
        <div className="min-h-0 flex-1 overflow-hidden">
          {mobileTab === 'problem' && <div className="h-full overflow-auto">{left}</div>}
          {mobileTab === 'code' && <div className="h-full overflow-hidden">{right}</div>}
          {mobileTab === 'output' && <div className="h-full overflow-auto">{bottom}</div>}
        </div>
      </div>
    )
  }

  return (
    <div
      ref={rootRef}
      className="flex min-h-0 flex-1 flex-col overflow-hidden"
      style={{ height: '100%' }}
    >
      <div className="flex min-h-0" style={{ height: `${100 - (bottom ? bottomPct : 0)}%` }}>
        <div className="min-w-0 overflow-auto pr-1" style={{ width: `${leftPct}%` }}>
          {left}
        </div>
        <button
          type="button"
          aria-label="Resize panels"
          className="w-1 shrink-0 cursor-col-resize bg-[var(--color-border)] hover:bg-[var(--color-accent)]"
          onPointerDown={() => {
            dragging.current = 'x'
            document.body.style.cursor = 'col-resize'
          }}
        />
        <div className="min-w-0 flex-1 overflow-hidden pl-1">{right}</div>
      </div>
      {bottom && (
        <>
          <button
            type="button"
            aria-label="Resize results"
            className="h-1 w-full cursor-row-resize bg-[var(--color-border)] hover:bg-[var(--color-accent)]"
            onPointerDown={() => {
              dragging.current = 'y'
              document.body.style.cursor = 'row-resize'
            }}
          />
          <div className="min-h-0 overflow-auto" style={{ height: `${bottomPct}%` }}>
            {bottom}
          </div>
        </>
      )}
    </div>
  )
}
