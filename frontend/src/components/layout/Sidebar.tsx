import { NavLink } from 'react-router-dom'
import { X } from 'lucide-react'

import { getNavIcon, navigationConfig } from '@/components/navigation/navConfig'
import { useAuth } from '@/hooks/useAuth'
import { cn } from '@/utils/cn'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin' || user?.role === 'trainer'
  return (
    <>
      <div
        className={cn(
          'fixed inset-0 z-40 bg-black/40 transition-opacity lg:hidden',
          open ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
        onClick={onClose}
        aria-hidden="true"
      />

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] transition-transform lg:static lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-[var(--color-border)] px-4">
          <div>
            <p className="text-sm font-semibold text-[var(--color-text)]">Job Ready</p>
            <p className="text-xs text-[var(--color-text-subtle)]">Platform</p>
          </div>
          <button
            type="button"
            className="rounded-md p-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-muted)] lg:hidden"
            onClick={onClose}
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {navigationConfig.map((section) => (
            <div key={section.title} className="mb-5">
              <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-subtle)]">
                {section.title}
              </p>
              <ul className="space-y-0.5">
                {section.items.map((item) => {
                  const Icon = getNavIcon(item.icon)
                  return (
                    <li key={item.path}>
                      <NavLink
                        to={item.path}
                        end={item.path === '/'}
                        onClick={onClose}
                        className={({ isActive }) =>
                          cn(
                            'flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors',
                            isActive
                              ? 'bg-[var(--color-accent-muted)] font-medium text-[var(--color-accent)]'
                              : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-muted)] hover:text-[var(--color-text)]',
                          )
                        }
                      >
                        <Icon className="h-4 w-4 shrink-0" />
                        <span className="truncate">{item.label}</span>
                      </NavLink>
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
          {isAdmin && (
            <div className="mb-5">
              <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-subtle)]">
                Admin
              </p>
              <ul className="space-y-0.5">
                {[
                  { label: 'Questions', path: '/admin/questions' },
                  { label: 'Taxonomy', path: '/admin/taxonomy' },
                  { label: 'AI Practice', path: '/admin/ai' },
                  { label: 'Cloud', path: '/admin/cloud' },
                  { label: 'DevOps', path: '/admin/devops' },
                  { label: 'Cybersecurity', path: '/admin/cybersecurity' },
                  { label: 'Scenarios', path: '/admin/scenarios' },
                  { label: 'Content Factory', path: '/admin/content' },
                  { label: 'Practice Paths', path: '/admin/practice-paths' },
                  { label: 'Courses', path: '/admin/courses' },
                  { label: 'Projects', path: '/admin/projects' },
                ].map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      onClick={onClose}
                      className={({ isActive }) =>
                        cn(
                          'flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors',
                          isActive
                            ? 'bg-[var(--color-accent-muted)] font-medium text-[var(--color-accent)]'
                            : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-muted)] hover:text-[var(--color-text)]',
                        )
                      }
                    >
                      {item.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </nav>
      </aside>
    </>
  )
}
