import { useEffect, useId, useRef, useState } from 'react'
import { Bell } from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/common/Button'
import { EmptyState, ErrorState, LoadingState } from '@/components/practice-workspace/PracticeWorkspace'
import { useAuth } from '@/hooks/useAuth'
import {
  fetchNotifications,
  fetchUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
  notificationDestination,
  type NotificationItem,
} from '@/services/notificationService'
import {
  notificationLoadFailed,
  notificationLoadMessage,
  notificationRefreshMessage,
} from '@/features/notifications/queryState'
import { EmailPreferences } from '@/features/notifications/EmailPreferences'

const REFRESH_MS = 60_000

function visibleInterval() {
  return document.visibilityState === 'visible' ? REFRESH_MS : false
}

export function NotificationBell() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [actionError, setActionError] = useState('')
  const buttonRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const titleId = useId()
  const userId = user?.id

  const unread = useQuery({
    queryKey: ['notification-unread', userId],
    queryFn: fetchUnreadCount,
    enabled: Boolean(userId),
    refetchInterval: visibleInterval,
    refetchIntervalInBackground: false,
  })
  const items = useQuery({
    queryKey: ['notifications', userId],
    queryFn: () => fetchNotifications(),
    enabled: Boolean(userId) && open,
    refetchInterval: open ? visibleInterval : false,
    refetchIntervalInBackground: false,
  })

  useEffect(() => {
    setOpen(false)
    setActionError('')
  }, [userId])

  useEffect(() => {
    function onOnline() {
      void queryClient.invalidateQueries({ queryKey: ['notification-unread', userId] })
      void queryClient.invalidateQueries({ queryKey: ['notifications', userId] })
    }
    window.addEventListener('online', onOnline)
    return () => window.removeEventListener('online', onOnline)
  }, [queryClient, userId])

  useEffect(() => {
    if (!open) return
    panelRef.current?.focus()
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpen(false)
        buttonRef.current?.focus()
      }
    }
    function onPointer(event: MouseEvent) {
      const target = event.target as Node
      if (panelRef.current?.contains(target) || buttonRef.current?.contains(target)) return
      setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    window.addEventListener('mousedown', onPointer)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('mousedown', onPointer)
    }
  }, [open])

  if (!userId) return null

  const count = unread.data?.count
  const label =
    typeof count === 'number'
      ? count === 0
        ? 'Notifications, no unread'
        : `Notifications, ${count} unread`
      : 'Notifications'

  async function refreshAll() {
    await Promise.all([unread.refetch(), items.refetch()])
  }

  async function openItem(item: NotificationItem) {
    setActionError('')
    const destination = notificationDestination(item.destination_path)
    if (!item.read_at) {
      try {
        await markNotificationRead(item.id)
        await refreshAll()
      } catch (error) {
        setActionError(error instanceof Error ? error.message : 'Could not mark this notification read.')
        return
      }
    }
    if (!destination) {
      setActionError('This notification does not have a page to open.')
      return
    }
    setOpen(false)
    navigate(destination)
  }

  async function markAll() {
    setActionError('')
    try {
      await markAllNotificationsRead()
      await refreshAll()
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Could not mark notifications read.')
    }
  }

  const refreshMessage = notificationRefreshMessage(items)
  const page = items.data

  return (
    <div className="notification-anchor">
      <button
        ref={buttonRef}
        type="button"
        className="icon-btn notification-bell"
        aria-label={label}
        aria-expanded={open}
        aria-controls="notification-panel"
        onClick={() => setOpen((current) => !current)}
      >
        <Bell className="h-4 w-4" aria-hidden />
        {typeof count === 'number' && count > 0 ? (
          <span className="notification-badge">{count > 9 ? '9+' : count}</span>
        ) : null}
      </button>
      {open ? (
        <div
          ref={panelRef}
          id="notification-panel"
          className="notification-panel"
          role="dialog"
          aria-labelledby={titleId}
          tabIndex={-1}
        >
          <div className="notification-panel-header">
            <h2 id={titleId}>Notifications</h2>
            <Button type="button" variant="secondary" size="sm" onClick={() => void markAll()} disabled={!count}>
              Mark all read
            </Button>
          </div>
          <EmailPreferences userId={userId} />
          {items.isLoading ? <LoadingState label="Loading notifications" /> : null}
          {notificationLoadFailed(items) ? (
            <div className="space-y-2">
              <ErrorState message={notificationLoadMessage(items.error, 'Could not load notifications.')} />
              <Button type="button" variant="secondary" size="sm" onClick={() => void items.refetch()}>
                Retry
              </Button>
            </div>
          ) : null}
          {refreshMessage ? (
            <div className="space-y-2">
              <ErrorState message={refreshMessage} />
              <Button type="button" variant="secondary" size="sm" onClick={() => void items.refetch()}>
                Retry
              </Button>
            </div>
          ) : null}
          {actionError ? <p className="text-sm text-[var(--color-danger)]">{actionError}</p> : null}
          {page && page.items.length === 0 ? (
            <EmptyState title="No notifications yet" description="Reviews and replies will show up here." />
          ) : null}
          {page && page.items.length > 0 ? (
            <ul className="notification-list">
              {page.items.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    className={item.read_at ? 'notification-item read' : 'notification-item unread'}
                    onClick={() => void openItem(item)}
                  >
                    <span className="notification-item-text">{item.message}</span>
                    <span className="notification-item-time">{new Date(item.created_at).toLocaleString()}</span>
                    <span className="notification-item-state">{item.read_at ? 'Read' : 'Unread'}</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
