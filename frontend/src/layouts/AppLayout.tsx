import { Outlet, useLocation } from 'react-router-dom'

import { Masthead } from '@/components/layout/Masthead'
import { navigationConfig, primaryNavItems } from '@/components/navigation/navConfig'
import { cn } from '@/utils/cn'

function getPageTitle(pathname: string): string {
  const primary = primaryNavItems.find((item) =>
    (item.match ?? [item.path]).some((prefix) =>
      prefix === '/' ? pathname === '/' : pathname === prefix || pathname.startsWith(`${prefix}/`),
    ),
  )
  if (primary && (primary.path === '/' ? pathname === '/' : pathname.startsWith(primary.path))) {
    return primary.label
  }
  for (const section of navigationConfig) {
    for (const item of section.items) {
      if (item.path === pathname) return item.label
    }
  }
  if (pathname.startsWith('/admin/assignments')) return 'Assignments'
  if (pathname.startsWith('/practice/sessions/')) return 'Practice session'
  return 'JobReady'
}

export function AppLayout() {
  const location = useLocation()
  const title = getPageTitle(location.pathname)
  const compact =
    location.pathname.startsWith('/practice/sessions/') ||
    location.pathname.startsWith('/practice/sql/') ||
    location.pathname.startsWith('/practice/dsa/')

  return (
    <div className={cn('flex min-h-full flex-col bg-[var(--color-surface-muted)]', 'app-shell-standard')}>
      <Masthead compact={compact} />
      <div className="jr-subheader">
        <p className="jr-breadcrumb">
          <span>Workspace</span>
          <span aria-hidden="true">/</span>
          <strong>{title}</strong>
        </p>
      </div>
      <main id="main-content" className="flex-1" tabIndex={-1}>
        <Outlet key={location.pathname} />
      </main>
    </div>
  )
}
