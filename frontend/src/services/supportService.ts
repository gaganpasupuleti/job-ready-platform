import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'

export const SUPPORT_CATEGORIES = [
  { value: 'bug', label: 'Bug' },
  { value: 'improvement', label: 'Improvement' },
  { value: 'feature_request', label: 'Feature request' },
  { value: 'general', label: 'General feedback' },
] as const

export const SUPPORT_STATUSES = [
  { value: 'new', label: 'New' },
  { value: 'in_review', label: 'In review' },
  { value: 'planned', label: 'Planned' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
] as const

export type SupportCategory = (typeof SUPPORT_CATEGORIES)[number]['value']
export type SupportStatus = (typeof SUPPORT_STATUSES)[number]['value']

export interface SupportTimelineItem {
  id: string
  kind: 'reply' | 'status'
  author_name: string
  author_role: string
  body: string | null
  from_status: string | null
  to_status: string | null
  created_at: string
}

export interface SupportTicketSummary {
  id: string
  reference: string
  category: SupportCategory
  title: string
  status: SupportStatus
  page_path: string | null
  created_at: string
  updated_at: string
}

export interface SupportTicketDetail extends SupportTicketSummary {
  description: string
  timeline: SupportTimelineItem[]
}

export interface AdminSupportTicketSummary extends SupportTicketSummary {
  student_name: string
  student_email: string
}

export interface AdminSupportTicketDetail extends SupportTicketDetail {
  student_name: string
  student_email: string
}

export interface SupportDraft {
  category: SupportCategory
  title: string
  description: string
  page_path: string | null
  client_request_id: string
}

export function supportLabel(options: readonly { value: string; label: string }[], value: string | null | undefined) {
  return options.find((item) => item.value === value)?.label ?? value ?? ''
}

export function currentSupportPagePath(pathname: string) {
  const clean = (pathname || '/').split('?')[0].split('#')[0]
  if (!clean.startsWith('/') || clean.length > 300) return '/'
  return clean
}

export function newClientRequestId() {
  return crypto.randomUUID().replace(/-/g, '')
}

export async function fetchMyTickets() {
  const { data } = await apiClient.get<SupportTicketSummary[]>(apiEndpoints.support.tickets)
  return data
}

export async function fetchMyTicket(id: string) {
  const { data } = await apiClient.get<SupportTicketDetail>(apiEndpoints.support.ticket(id))
  return data
}

export async function createSupportTicket(payload: SupportDraft) {
  const { data } = await apiClient.post<SupportTicketDetail>(apiEndpoints.support.tickets, payload)
  return data
}

export async function replyToMyTicket(id: string, body: string, clientRequestId: string) {
  const { data } = await apiClient.post<SupportTicketDetail>(apiEndpoints.support.replies(id), {
    body,
    client_request_id: clientRequestId,
  })
  return data
}

export async function fetchAdminTickets(filters: {
  category?: string
  status?: string
  date_from?: string
  date_to?: string
}) {
  const { data } = await apiClient.get<AdminSupportTicketSummary[]>(apiEndpoints.admin.supportTickets, {
    params: filters,
  })
  return data
}

export async function fetchAdminTicket(id: string) {
  const { data } = await apiClient.get<AdminSupportTicketDetail>(apiEndpoints.admin.supportTicket(id))
  return data
}

export async function replyToAdminTicket(id: string, body: string, clientRequestId: string) {
  const { data } = await apiClient.post<AdminSupportTicketDetail>(apiEndpoints.admin.supportReplies(id), {
    body,
    client_request_id: clientRequestId,
  })
  return data
}

export async function updateAdminTicketStatus(id: string, status: SupportStatus, clientRequestId: string) {
  const { data } = await apiClient.patch<AdminSupportTicketDetail>(apiEndpoints.admin.supportTicket(id), {
    status,
    client_request_id: clientRequestId,
  })
  return data
}
