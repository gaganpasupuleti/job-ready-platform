import type { ComponentType } from 'react'
import {
  Award,
  Bookmark,
  Bot,
  Brain,
  Briefcase,
  Building2,
  Cloud,
  Code2,
  Database,
  FileQuestion,
  Flame,
  LayoutDashboard,
  ListChecks,
  MessageSquare,
  Server,
  Shield,
  Sparkles,
  Target,
  Terminal,
  Trophy,
  Users,
  Wrench,
} from 'lucide-react'

import type { NavSection } from '@/types'

/** Primary horizontal nav — Jobs is the jobs-first destination; other routes stay. */
export const primaryNavItems: { label: string; path: string; match?: string[] }[] = [
  { label: 'Jobs', path: '/jobs', match: ['/jobs'] },
  { label: 'Overview', path: '/', match: ['/'] },
  { label: 'Practice', path: '/practice', match: ['/practice'] },
  { label: 'Learn', path: '/learn', match: ['/learn'] },
  { label: 'Playground', path: '/practice/playground', match: ['/practice/playground', '/practice/python'] },
  {
    label: 'Assessments',
    path: '/practice/aptitude',
    match: ['/practice/aptitude', '/practice/mcq', '/practice/sessions', '/assessments'],
  },
  { label: 'Review', path: '/mistakes', match: ['/mistakes'] },
]

/** Secondary destinations kept reachable (More drawer / footer links). */
export const navigationConfig: NavSection[] = [
  {
    title: 'Today',
    items: [
      { label: 'Jobs', path: '/jobs', icon: 'Briefcase' },
      { label: 'Overview', path: '/', icon: 'LayoutDashboard' },
      { label: 'Practice', path: '/practice', icon: 'Target' },
      { label: 'Learn', path: '/learn', icon: 'ListChecks' },
      { label: 'Playground', path: '/practice/playground', icon: 'Terminal' },
      { label: 'Assessments', path: '/practice/aptitude', icon: 'FileQuestion' },
      { label: 'Review', path: '/mistakes', icon: 'FileQuestion' },
    ],
  },
  {
    title: 'Practice tracks',
    items: [
      { label: 'SQL', path: '/practice/sql', icon: 'Database' },
      { label: 'DSA', path: '/practice/dsa', icon: 'Code2' },
      { label: 'Coding', path: '/practice/coding', icon: 'Terminal' },
      { label: 'Technical MCQs', path: '/practice/mcq', icon: 'FileQuestion' },
      { label: 'Aptitude / CRT', path: '/practice/aptitude', icon: 'Brain' },
      { label: 'Projects', path: '/practice/projects', icon: 'Wrench' },
    ],
  },
  {
    title: 'More',
    items: [
      { label: 'Job Readiness', path: '/readiness', icon: 'Target' },
      { label: 'AI Home', path: '/ai', icon: 'Sparkles' },
      { label: 'Prompt Engineering', path: '/ai/prompt-engineering', icon: 'MessageSquare' },
      { label: 'Cloud', path: '/cloud', icon: 'Cloud' },
      { label: 'DevOps', path: '/devops', icon: 'Wrench' },
      { label: 'Cybersecurity', path: '/cybersecurity', icon: 'Shield' },
      { label: 'Interview Prep', path: '/interviews', icon: 'Users' },
      { label: 'Bookmarks', path: '/bookmarks', icon: 'Bookmark' },
      { label: 'Recommended Jobs', path: '/jobs/recommended', icon: 'Target' },
      { label: 'Applications', path: '/jobs/applications', icon: 'Award' },
    ],
  },
]

export const JOBS_HOME = '/jobs'
export const JOBS_PREFERENCES = '/jobs/preferences'
export const JOBS_ONBOARDING_KEY = 'jr_jobs_onboarding'

const iconMap: Record<string, ComponentType<{ className?: string }>> = {
  LayoutDashboard,
  Brain,
  Code2,
  Terminal,
  Database,
  FileQuestion,
  Sparkles,
  Bot,
  MessageSquare,
  Users,
  Cloud,
  Wrench,
  Shield,
  Building2,
  ListChecks,
  Trophy,
  Briefcase,
  Target,
  Bookmark,
  Award,
  Flame,
  Server,
}

export function getNavIcon(name?: string) {
  if (!name) return LayoutDashboard
  return iconMap[name] ?? LayoutDashboard
}

export function isPrimaryNavActive(pathname: string, item: (typeof primaryNavItems)[number]) {
  if (item.path === '/') return pathname === '/'
  let winner: { path: string; length: number } | null = null
  for (const candidate of primaryNavItems) {
    if (candidate.path === '/') continue
    for (const prefix of candidate.match ?? [candidate.path]) {
      if (prefix === '/') continue
      const hit = pathname === prefix || pathname.startsWith(`${prefix}/`)
      if (hit && (!winner || prefix.length > winner.length)) {
        winner = { path: candidate.path, length: prefix.length }
      }
    }
  }
  return winner?.path === item.path
}
