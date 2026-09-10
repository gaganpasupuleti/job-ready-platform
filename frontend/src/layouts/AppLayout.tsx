import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { navigationConfig } from '@/components/navigation/navConfig'
import { cn } from '@/utils/cn'

function getPageTitle(pathname: string): string {
  for (const section of navigationConfig) {
    for (const item of section.items) {
      if (item.path === pathname) return item.label
    }
  }
  if (pathname === '/') return 'Dashboard'
  if (pathname.startsWith('/practice/python') || pathname.startsWith('/practice/playground')) {
    return 'Python Playground'
  }
  if (pathname.startsWith('/practice/dsa/')) return 'Coding workspace'
  if (pathname.startsWith('/practice/sql/')) return 'SQL workspace'
  if (pathname.startsWith('/practice/sessions/')) return 'Practice session'
  return 'Job Ready Platform'
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
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const title = getPageTitle(location.pathname)
  const shell = resolveShell(location.pathname)
  const hideChromeTitle = shell === 'focused'

  return (
    <div
      className={cn(
        'flex min-h-full bg-[var(--color-surface-muted)]',
        shell === 'standard' && 'app-shell-standard',
        shell === 'focused' && 'app-shell-focused',
        shell === 'assessment' && 'app-shell-assessment',
      )}
      data-shell={shell}
    >
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex min-h-full min-w-0 flex-1 flex-col">
        <Header
          title={hideChromeTitle ? '' : title}
          onMenuClick={() => setSidebarOpen(true)}
          compact={shell !== 'standard'}
        />
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
