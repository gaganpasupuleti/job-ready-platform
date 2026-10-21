import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { ChevronDown, Search, X } from 'lucide-react'

import {
  categoryForPath,
  exploreCategoryLabels,
  exploreCategoriesForUser,
  filterExploreDestinations,
  isExploreRouteActive,
  resolveExploreDestination,
  type ExploreCategoryId,
  type ExploreDestination,
} from '@/components/navigation/exploreNavRegistry'
import { cn } from '@/utils/cn'

interface ExploreLauncherProps {
  isAdmin: boolean
  open: boolean
  onOpenChange: (open: boolean) => void
  onCloseMobileNav?: () => void
  mobileSheet?: boolean
}

export function ExploreLauncher({
  isAdmin,
  open,
  onOpenChange,
  onCloseMobileNav,
  mobileSheet = false,
}: ExploreLauncherProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const rootRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<ExploreCategoryId>(() => categoryForPath(location.pathname, isAdmin))

  const exploreActive = isExploreRouteActive(location.pathname, isAdmin)
  const categories = exploreCategoriesForUser(isAdmin)

  useEffect(() => {
    if (!open) {
      setQuery('')
      return
    }
    setCategory(categoryForPath(location.pathname, isAdmin))
    queueMicrotask(() => searchRef.current?.focus())
  }, [open, location.pathname, isAdmin])

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onOpenChange(false)
        triggerRef.current?.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onOpenChange])

  const filtered = useMemo(() => filterExploreDestinations(query, isAdmin), [query, isAdmin])

  const panelDestinations = useMemo(() => {
    if (query.trim()) {
      return filtered.sort((a, b) => a.label.localeCompare(b.label))
    }
    return filtered.filter((dest) => dest.category === category)
  }, [filtered, query, category])

  const activeDest = resolveExploreDestination(location.pathname, isAdmin)

  function go(dest: ExploreDestination) {
    onOpenChange(false)
    onCloseMobileNav?.()
    navigate(dest.path)
  }

  if (mobileSheet) {
    if (!open) return null
    return (
      <div className="explore-sheet-backdrop" role="presentation" onClick={() => onOpenChange(false)}>
        <div
          className="explore-sheet"
          role="dialog"
          aria-modal="true"
          aria-label="Explore destinations"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="explore-sheet-header">
            <h2 className="explore-sheet-title">Explore</h2>
            <button type="button" className="explore-sheet-close" onClick={() => onOpenChange(false)}>
              <X size={18} aria-hidden /> Close
            </button>
          </div>
          <ExplorePanelBody
            query={query}
            onQueryChange={setQuery}
            searchRef={searchRef}
            categories={categories}
            category={category}
            onCategoryChange={setCategory}
            destinations={panelDestinations}
            searchMode={Boolean(query.trim())}
            activePath={activeDest?.path}
            onSelect={go}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="explore-nav" ref={rootRef}>
      <button
        ref={triggerRef}
        type="button"
        className={cn('explore-nav-trigger nav-item', open && 'open', exploreActive && 'is-route-active')}
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-controls="explore-launcher-panel"
        onClick={() => onOpenChange(!open)}
      >
        Explore
        <ChevronDown className="more-chevron" aria-hidden />
      </button>
      {open ? (
        <div
          id="explore-launcher-panel"
          className="explore-popover"
          role="dialog"
          aria-label="Explore destinations"
        >
          <ExplorePanelBody
            query={query}
            onQueryChange={setQuery}
            searchRef={searchRef}
            categories={categories}
            category={category}
            onCategoryChange={setCategory}
            destinations={panelDestinations}
            searchMode={Boolean(query.trim())}
            activePath={activeDest?.path}
            onSelect={go}
          />
        </div>
      ) : null}
    </div>
  )
}

function ExplorePanelBody({
  query,
  onQueryChange,
  searchRef,
  categories,
  category,
  onCategoryChange,
  destinations,
  searchMode,
  activePath,
  onSelect,
}: {
  query: string
  onQueryChange: (value: string) => void
  searchRef: React.RefObject<HTMLInputElement | null>
  categories: ExploreCategoryId[]
  category: ExploreCategoryId
  onCategoryChange: (id: ExploreCategoryId) => void
  destinations: ExploreDestination[]
  searchMode: boolean
  activePath?: string
  onSelect: (dest: ExploreDestination) => void
}) {
  return (
    <>
      <div className="explore-search-wrap">
        <Search size={16} className="explore-search-icon" aria-hidden />
        <input
          ref={searchRef}
          type="search"
          className="explore-search"
          placeholder="Find a destination"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          aria-label="Find a destination"
        />
      </div>
      <div className="explore-body">
        {!searchMode ? (
          <div className="explore-rail" role="tablist" aria-label="Categories">
            {categories.map((id) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={category === id}
                className={cn('explore-rail-item', category === id && 'is-selected')}
                onClick={() => onCategoryChange(id)}
              >
                {exploreCategoryLabels[id]}
              </button>
            ))}
          </div>
        ) : null}
        <div className="explore-panel" role="tabpanel">
          {destinations.length === 0 ? (
            <p className="explore-empty">No destinations match your search.</p>
          ) : (
            <ul className="explore-dest-list">
              {destinations.map((dest) => {
                const active = activePath === dest.path
                return (
                  <li key={dest.path}>
                    <button
                      type="button"
                      className={cn('explore-dest-row', active && 'is-active')}
                      onClick={() => onSelect(dest)}
                    >
                      <span className="explore-dest-label">{dest.label}</span>
                      {searchMode ? (
                        <span className="explore-dest-category">{exploreCategoryLabels[dest.category]}</span>
                      ) : null}
                      <span className="explore-dest-desc">{dest.description}</span>
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </div>
    </>
  )
}

/** Mobile-only trigger placed in masthead tools when nav is collapsed. */
export function ExploreMobileTrigger({
  isAdmin,
  open,
  onOpenChange,
}: {
  isAdmin: boolean
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const location = useLocation()
  const exploreActive = isExploreRouteActive(location.pathname, isAdmin)
  return (
    <>
      <button
        type="button"
        className={cn('explore-mobile-trigger', exploreActive && 'is-route-active')}
        aria-expanded={open}
        onClick={() => onOpenChange(!open)}
      >
        Explore
      </button>
      <ExploreLauncher isAdmin={isAdmin} open={open} onOpenChange={onOpenChange} mobileSheet />
    </>
  )
}
