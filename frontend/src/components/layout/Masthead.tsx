import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronDown, LogOut, Menu, Moon, Sun, X } from 'lucide-react'

import { Logo } from '@/components/brand/Logo'
import { Button } from '@/components/common/Button'
import { isPrimaryNavActive, navigationConfig, primaryNavItems } from '@/components/navigation/navConfig'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/utils/cn'

const ADMIN_LINKS = [
  { label: 'Questions', path: '/admin/questions' },
  { label: 'Jobs', path: '/admin/jobs' },
  { label: 'Assignments', path: '/admin/assignments' },
  { label: 'Projects', path: '/admin/projects' },
  { label: 'Readiness', path: '/admin/readiness' },
]

export function Masthead({ compact = false }: { compact?: boolean }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [moreOpen, setMoreOpen] = useState(false)
  const location = useLocation()
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const isAdmin = user?.role === 'admin' || user?.role === 'trainer'
  const initials = useMemo(() => {
    const source = user?.full_name || user?.username || 'JR'
    return source
      .split(/\s+/)
      .map((part) => part[0])
      .join('')
      .slice(0, 2)
      .toUpperCase()
  }, [user])

  const primaryPaths = new Set(primaryNavItems.map((item) => item.path))
  const moreItems = navigationConfig.flatMap((section) =>
    section.items.filter((item) => !primaryPaths.has(item.path)),
  )
  const closeMobile = () => setMobileOpen(false)

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className={cn('masthead', compact && 'masthead-compact')}>
        <Link to="/jobs" className="new-brand" aria-label="JobReady jobs" onClick={closeMobile}>
          <Logo />
        </Link>
        <nav className={cn('main-navigation', mobileOpen && 'mobile-open')} aria-label="Main navigation">
          {primaryNavItems.map((item) => {
            const active = isPrimaryNavActive(location.pathname, item)
            return (
              <Link
                key={item.path + item.label}
                to={item.path}
                className={active ? 'active' : undefined}
                aria-current={active ? 'page' : undefined}
                onClick={closeMobile}
              >
                {item.label}
              </Link>
            )
          })}
          <div className="more-nav">
            <button
              type="button"
              className={cn('more-nav-trigger', moreOpen && 'open')}
              aria-expanded={moreOpen}
              onClick={() => setMoreOpen((open) => !open)}
            >
              More
              <ChevronDown className="h-3.5 w-3.5" aria-hidden />
            </button>
            {moreOpen ? (
              <div className="more-nav-panel" role="menu">
                {moreItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    role="menuitem"
                    onClick={() => {
                      setMoreOpen(false)
                      closeMobile()
                    }}
                  >
                    {item.label}
                  </Link>
                ))}
                {isAdmin
                  ? ADMIN_LINKS.map((item) => (
                      <Link
                        key={item.path}
                        to={item.path}
                        role="menuitem"
                        onClick={() => {
                          setMoreOpen(false)
                          closeMobile()
                        }}
                      >
                        {item.label}
                      </Link>
                    ))
                  : null}
              </div>
            ) : null}
          </div>
        </nav>
        <div className="masthead-tools">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            className="icon-btn"
          >
            {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </Button>
          {user ? (
            <button
              type="button"
              className="profile-button"
              aria-label={`Signed in as ${user.username}. Log out`}
              onClick={() => logout()}
            >
              {initials}
            </button>
          ) : null}
          <button
            type="button"
            className="menu-toggle icon-btn"
            aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'}
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((open) => !open)}
          >
            {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
          {user ? (
            <Button variant="ghost" size="sm" className="logout-desktop" onClick={() => logout()} aria-label="Logout">
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          ) : null}
        </div>
      </header>
      {mobileOpen ? (
        <button type="button" className="mobile-backdrop" aria-label="Close navigation" onClick={closeMobile} />
      ) : null}
    </>
  )
}
