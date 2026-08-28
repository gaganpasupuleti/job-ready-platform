import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { navigationConfig } from '@/components/navigation/navConfig'

function getPageTitle(pathname: string): string {
  for (const section of navigationConfig) {
    for (const item of section.items) {
      if (item.path === pathname) return item.label
    }
  }
  if (pathname === '/') return 'Dashboard'
  return 'Job Ready Platform'
}

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const title = getPageTitle(location.pathname)

  return (
    <div className="flex min-h-full bg-[var(--color-surface-muted)]">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex min-h-full min-w-0 flex-1 flex-col">
        <Header title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
