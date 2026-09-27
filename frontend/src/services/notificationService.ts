import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export type NotificationItem = {
  id: string
  event_type: 'assignment_review' | 'support_reply'
  message: string
  destination_path: string
  created_at: string
  read_at: string | null
}

export type NotificationPage = {
  items: NotificationItem[]
  next_cursor: string | null
}

const ASSIGNMENT_DESTINATION = /^\/practice\/projects#submission-[0-9a-f-]{36}$/i
const SUPPORT_DESTINATION = /^\/support\/requests\/[0-9a-f-]{36}$/i

export function notificationDestination(path: string): string | null {
  if (ASSIGNMENT_DESTINATION.test(path) || SUPPORT_DESTINATION.test(path)) return path
  return null
}

export async function fetchNotifications(cursor?: string | null) {
  const { data } = await apiClient.get<NotificationPage>(apiEndpoints.notifications.list, {
    params: { limit: 20, cursor: cursor || undefined },
  })
  return data
}

export async function fetchUnreadCount() {
  const { data } = await apiClient.get<{ count: number }>(apiEndpoints.notifications.unread)
  return data
}

export async function markNotificationRead(id: string) {
  const { data } = await apiClient.post<NotificationItem>(apiEndpoints.notifications.read(id))
  return data
}

export async function markAllNotificationsRead() {
  const { data } = await apiClient.post<{ count: number }>(apiEndpoints.notifications.readAll)
  return data
}
