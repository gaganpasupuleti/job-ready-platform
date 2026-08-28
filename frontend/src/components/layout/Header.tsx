import { Link } from 'react-router-dom'
import { LogOut, Menu, Moon, Sun, Wifi, WifiOff } from 'lucide-react'

import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { useAuth } from '@/hooks/useAuth'
import { useHealth } from '@/hooks/usePlatform'
import { useTheme } from '@/hooks/useTheme'

interface HeaderProps {
  onMenuClick: () => void
  title: string
}

export function Header({ onMenuClick, title }: HeaderProps) {
  const { theme, toggleTheme } = useTheme()
  const { user, logout } = useAuth()
  const { data: health, isSuccess, isError } = useHealth()

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-4 border-b border-[var(--color-border)] bg-[var(--color-surface)]/95 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="rounded-md p-2 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-muted)] lg:hidden"
          onClick={onMenuClick}
          aria-label="Open navigation"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-sm font-semibold text-[var(--color-text)] sm:text-base">{title}</h1>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {user && (user.role === 'admin' || user.role === 'trainer') && (
          <Link to="/admin/questions" className="hidden text-xs text-[var(--color-accent)] sm:block">
            Admin
          </Link>
        )}
        {user && (
          <span className="hidden text-xs text-[var(--color-text-muted)] sm:inline">
            {user.username}
          </span>
        )}
        <Badge
          variant={isSuccess ? 'success' : isError ? 'warning' : 'default'}
          className="hidden items-center gap-1 sm:inline-flex"
        >
          {isSuccess ? (
            <>
              <Wifi className="h-3 w-3" />
              API {health?.status}
            </>
          ) : isError ? (
            <>
              <WifiOff className="h-3 w-3" />
              API offline
            </>
          ) : (
            'Connecting…'
          )}
        </Badge>

        <Button
          variant="ghost"
          size="sm"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>

        {user && (
          <Button variant="ghost" size="sm" onClick={() => logout()} aria-label="Logout">
            <LogOut className="h-4 w-4" />
          </Button>
        )}
      </div>
    </header>
  )
}
