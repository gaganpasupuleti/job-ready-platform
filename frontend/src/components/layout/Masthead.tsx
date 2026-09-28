import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronDown, LogOut, Menu, Moon, Sun, X } from 'lucide-react'

import { Logo } from '@/components/brand/Logo'
import { Button } from '@/components/common/Button'
import { NotificationBell } from '@/features/notifications/NotificationBell'
import { FeedbackPanel } from '@/features/support/FeedbackPanel'
import {
  isPrimaryNavActive,
  moreMenuGroups,
  primaryNavItems,
} from '@/components/navigation/navConfig'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/utils/cn'

function isMoreItemActive(pathname: string, path: string) {
  const paths = moreMenuGroups.flatMap((group) => group.items.map((item) => item.path))
  const matches = paths.filter((candidate) => pathname === candidate || pathname.startsWith(`${candidate}/`))
  if (!matches.includes(path)) return false
  const best = matches.reduce((longest, candidate) => (candidate.length > longest.length ? candidate : longest))
  return best === path
}

interface MastheadProps {
  compact?: boolean
}

export function Masthead({ compact = false }: MastheadProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [moreOpen, setMoreOpen] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const moreRef = useRef<HTMLDivElement>(null)
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

  const closeMobile = () => setMobileOpen(false)
  const closeMore = () => setMoreOpen(false)

  useEffect(() => {
    if (!moreOpen) return
    const onPointer = (event: MouseEvent) => {
      if (!moreRef.current?.contains(event.target as Node)) closeMore()
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') closeMore()
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [moreOpen])

  useEffect(() => {
    if (!feedbackOpen) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setFeedbackOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [feedbackOpen])

  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className={cn('masthead', compact && 'masthead-compact')}>
        <Link to="/" className="new-brand" aria-label="JobReady overview" onClick={closeMobile}>
          <Logo />
        </Link>

        <nav
          className={cn('main-navigation', mobileOpen && 'mobile-open')}
          aria-label="Main navigation"
        >
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
          <div className="more-nav" ref={moreRef}>
            <button
              type="button"
              className={cn('more-nav-trigger nav-item', moreOpen && 'open')}
              aria-expanded={moreOpen}
              aria-haspopup="true"
              onClick={() => setMoreOpen((v) => !v)}
            >
              More
              <ChevronDown className="more-chevron" aria-hidden />
            </button>
            {moreOpen ? (
              <div className="more-nav-panel" aria-label="More destinations">
                {user ? (
                  <button
                    type="button"
                    className="more-menu-item feedback-entry-menu"
                    onClick={() => {
                      setFeedbackOpen(true)
                      closeMore()
                      closeMobile()
                    }}
                  >
                    Feedback
                  </button>
                ) : null}
                {moreMenuGroups.map((group) => (
                  <section key={group.title} className="more-menu-section">
                    <p className="menu-section-title">{group.title}</p>
                    {group.items.map((item) => {
                      const active = isMoreItemActive(location.pathname, item.path)
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          className={cn('more-menu-item', active && 'active')}
                          aria-current={active ? 'page' : undefined}
                          onClick={() => {
                            closeMore()
                            closeMobile()
                          }}
                        >
                          {item.label}
                        </Link>
                      )
                    })}
                  </section>
                ))}
                {isAdmin ? (
                  <>
                    <p className="menu-section-title">Admin</p>
                    <Link
                      to="/admin/questions"
                      className={cn(
                        'more-menu-item more-menu-admin',
                        (location.pathname === '/admin/questions' || location.pathname.startsWith('/admin/')) && 'active',
                      )}
                      aria-current={location.pathname.startsWith('/admin') ? 'page' : undefined}
                      onClick={() => {
                        closeMore()
                        closeMobile()
                      }}
                    >
                      Admin
                    </Link>
                    <Link
                      to="/admin/library"
                      className={cn('more-menu-item more-menu-admin', location.pathname.startsWith('/admin/library') && 'active')}
                      onClick={() => {
                        closeMore()
                        closeMobile()
                      }}
                    >
                      Library
                    </Link>
                    <Link
                      to="/admin/feedback"
                      className={cn('more-menu-item more-menu-admin', location.pathname.startsWith('/admin/feedback') && 'active')}
                      onClick={() => {
                        closeMore()
                        closeMobile()
                      }}
                    >
                      Student Feedback
                    </Link>
                  </>
                ) : null}
              </div>
            ) : null}
          </div>
        </nav>

        <div className="masthead-tools">
          {user ? (
            <Button
              variant="ghost"
              size="sm"
              className="feedback-entry"
              aria-expanded={feedbackOpen}
              onClick={() => setFeedbackOpen((open) => !open)}
            >
              Feedback
            </Button>
          ) : null}
          {user ? <NotificationBell /> : null}
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
              title={`${user.username} · Log out`}
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
            onClick={() => setMobileOpen((v) => !v)}
          >
            {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
          {user ? (
            <Button
              variant="ghost"
              size="sm"
              className="logout-desktop"
              onClick={() => logout()}
              aria-label="Logout"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          ) : null}
        </div>
      </header>
      {mobileOpen ? (
        <button
          type="button"
          className="mobile-backdrop"
          aria-label="Close navigation"
          onClick={closeMobile}
        />
      ) : null}
      <FeedbackPanel open={feedbackOpen} onClose={() => setFeedbackOpen(false)} />
    </>
  )
}
