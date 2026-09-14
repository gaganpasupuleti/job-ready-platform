import { Outlet, useLocation } from 'react-router-dom'

import { Masthead } from '@/components/layout/Masthead'
import { navigationConfig } from '@/components/navigation/navConfig'
import { cn } from '@/utils/cn'

function getPageTitle(pathname: string): string {
  for (const section of navigationConfig) {
    for (const item of section.items) {
      if (item.path === pathname) return item.label
    }
  }
  if (pathname === '/') return 'Overview'
  if (pathname.startsWith('/practice/python') || pathname.startsWith('/practice/playground')) {
    return 'Playground'
  }
  if (pathname.startsWith('/practice/dsa/')) return 'Coding workspace'
  if (pathname.startsWith('/practice/sql/')) return 'SQL workspace'
  if (pathname.startsWith('/practice/sessions/')) return 'Practice session'
  return 'JobReady'
}

type ShellMode = 'standard' | 'focused' | 'assessment'

function resolveShell(pathname: string): ShellMode {
  if (
    pathname.startsWith('/practice/dsa/') ||
    pathname.startsWith('/practice/sql/') ||
    pathname.startsWith('/practice/python') ||
    pathname.startsWith('/practice/playground') ||
    (pathname.startsWith('/learn/courses/') && pathname.includes('/lessons/'))
  ) {
    return 'focused'
  }
  if (
    pathname.startsWith('/practice/sessions/') ||
    pathname.startsWith('/assessments') ||
    pathname.includes('/exam')
  ) {
    return 'assessment'
  }
  return 'standard'
}

export function AppLayout() {
  const location = useLocation()
  const title = getPageTitle(location.pathname)
  const shell = resolveShell(location.pathname)
  const compact = shell !== 'standard'
  const wide = shell === 'standard' && location.pathname.startsWith('/jobs') && location.pathname !== '/jobs/preferences'

  return (
    <div
      className={cn(
        'flex min-h-full flex-col bg-[var(--color-surface-muted)]',
        shell === 'standard' && 'app-shell-standard',
        shell === 'focused' && 'app-shell-focused',
        shell === 'assessment' && 'app-shell-assessment',
      )}
      data-shell={shell}
      data-layout={wide ? 'wide' : 'reading'}
    >
      <Masthead compact={compact} />
      {shell === 'standard' ? (
        <div className="jr-subheader">
          <p className="jr-breadcrumb">
            <span>Workspace</span>
            <span aria-hidden="true">/</span>
            <strong>{title}</strong>
          </p>
        </div>
      ) : null}
      <main id="main-content" className="flex-1" tabIndex={-1}>
        <div key={location.pathname} className="page-enter">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
