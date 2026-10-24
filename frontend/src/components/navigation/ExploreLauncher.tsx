import { useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronDown } from 'lucide-react'

import {
  exploreCategoryLabels,
  exploreCategoriesForUser,
  isExploreRouteActive,
  visibleExploreDestinations,
} from '@/components/navigation/exploreNavRegistry'
import { cn } from '@/utils/cn'

interface MoreDestinationsPanelProps {
  isAdmin: boolean
  onNavigate?: () => void
}

function MoreDestinationsPanel({ isAdmin, onNavigate }: MoreDestinationsPanelProps) {
  const location = useLocation()
  const categories = exploreCategoriesForUser(isAdmin)
  const destinations = visibleExploreDestinations(isAdmin)

  return (
    <div className="more-mega-panel" role="region" aria-label="More destinations">
      {categories.map((categoryId) => {
        const items = destinations.filter((dest) => dest.category === categoryId)
        if (items.length === 0) return null
        return (
          <section key={categoryId} className="more-mega-section">
            <h3 className="more-mega-heading">{exploreCategoryLabels[categoryId]}</h3>
            <ul className="more-pill-grid">
              {items.map((dest) => {
                const active =
                  location.pathname === dest.path || location.pathname.startsWith(`${dest.path}/`)
                return (
                  <li key={dest.path}>
                    <Link
                      to={dest.path}
                      className={cn('more-pill', active && 'is-active')}
                      aria-current={active ? 'page' : undefined}
                      onClick={onNavigate}
                    >
                      {dest.label}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </section>
        )
      })}
    </div>
  )
}

interface MoreMenuProps {
  isAdmin: boolean
  open: boolean
  onOpenChange: (open: boolean) => void
  onCloseMobileNav?: () => void
  mobileInline?: boolean
}

export function MoreMenu({
  isAdmin,
  open,
  onOpenChange,
  onCloseMobileNav,
  mobileInline = false,
}: MoreMenuProps) {
  const location = useLocation()
  const triggerRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const moreActive = isExploreRouteActive(location.pathname, isAdmin)

  useEffect(() => {
    if (!open || mobileInline) return
    const firstLink = panelRef.current?.querySelector<HTMLAnchorElement>('a.more-pill')
    firstLink?.focus()
  }, [open, mobileInline])

  useEffect(() => {
    if (!open || mobileInline) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onOpenChange(false)
        triggerRef.current?.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onOpenChange, mobileInline])

  const close = () => {
    onOpenChange(false)
    onCloseMobileNav?.()
  }

  if (mobileInline) {
    return (
      <div className="more-nav more-nav--inline">
        <MoreDestinationsPanel isAdmin={isAdmin} onNavigate={onCloseMobileNav} />
      </div>
    )
  }

  return (
    <div className="more-nav">
      <button
        ref={triggerRef}
        type="button"
        className={cn('more-nav-trigger nav-item', open && 'open', moreActive && 'is-route-active')}
        aria-expanded={open}
        aria-haspopup="true"
        aria-controls="more-mega-panel"
        onClick={() => onOpenChange(!open)}
      >
        More
        <ChevronDown className="more-chevron" aria-hidden />
      </button>
      {open ? (
        <div id="more-mega-panel" ref={panelRef} className="more-mega-popover">
          <MoreDestinationsPanel isAdmin={isAdmin} onNavigate={close} />
        </div>
      ) : null}
    </div>
  )
}

export const ExploreLauncher = MoreMenu

export function ExploreMobileTrigger() {
  return null
}
