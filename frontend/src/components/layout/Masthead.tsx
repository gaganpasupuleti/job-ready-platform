import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, Moon, Sun, X } from 'lucide-react'

import { Logo } from '@/components/brand/Logo'
import { Button } from '@/components/common/Button'
import { ExploreLauncher, ExploreMobileTrigger } from '@/components/navigation/ExploreLauncher'
import { isPrimaryNavActive, primaryNavItems } from '@/components/navigation/navConfig'
import { NotificationBell } from '@/features/notifications/NotificationBell'
import { FeedbackPanel } from '@/features/support/FeedbackPanel'
import { useAuth } from '@/hooks/useAuth'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/utils/cn'

interface MastheadProps {
  compact?: boolean
}

export function Masthead({ compact = false }: MastheadProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [exploreOpen, setExploreOpen] = useState(false)
  const [accountOpen, setAccountOpen] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const accountRef = useRef<HTMLDivElement>(null)
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

  useEffect(() => {
    setExploreOpen(false)
    setAccountOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!accountOpen) return
    const onPointer = (event: MouseEvent) => {
      if (!accountRef.current?.contains(event.target as Node)) setAccountOpen(false)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      setAccountOpen(false)
      accountRef.current?.querySelector('button')?.focus()
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [accountOpen])

  useEffect(() => {
    if (!exploreOpen) return
    const onPointer = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (target.closest('.explore-nav') || target.closest('.explore-sheet')) return
      if (target.closest('.explore-mobile-trigger')) return
      setExploreOpen(false)
    }
    document.addEventListener('mousedown', onPointer)
    return () => document.removeEventListener('mousedown', onPointer)
  }, [exploreOpen])

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
          <ExploreLauncher
            isAdmin={isAdmin}
            open={exploreOpen}
            onOpenChange={(next) => {
              if (next) setAccountOpen(false)
              setExploreOpen(next)
            }}
            onCloseMobileNav={closeMobile}
          />
        </nav>

        <div className="masthead-tools">
          <ExploreMobileTrigger
            isAdmin={isAdmin}
            open={exploreOpen}
            onOpenChange={(next) => {
              if (next) setAccountOpen(false)
              setExploreOpen(next)
            }}
          />
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
            <div className="account-nav" ref={accountRef}>
              <button
                type="button"
                className="profile-button"
                aria-label={`Account menu for ${user.full_name || user.username}`}
                aria-haspopup="menu"
                aria-expanded={accountOpen}
                aria-controls="account-menu"
                onClick={() => {
                  setExploreOpen(false)
                  setAccountOpen((open) => {
                    const next = !open
                    if (next) {
                      queueMicrotask(() => accountRef.current?.querySelector('a')?.focus())
                    }
                    return next
                  })
                }}
              >
                {initials}
              </button>
              {accountOpen ? (
                <div id="account-menu" className="account-menu" role="menu" aria-label="Account">
                  <p className="account-identity">{user.full_name || user.username}</p>
                  <Link role="menuitem" to="/jobs/preferences" onClick={() => setAccountOpen(false)}>
                    Job preferences
                  </Link>
                  <Link role="menuitem" to="/readiness" onClick={() => setAccountOpen(false)}>
                    Readiness
                  </Link>
                  <button
                    type="button"
                    role="menuitem"
                    className="account-menu-action"
                    onClick={() => {
                      setAccountOpen(false)
                      logout()
                    }}
                  >
                    Sign out
                  </button>
                </div>
              ) : null}
            </div>
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
