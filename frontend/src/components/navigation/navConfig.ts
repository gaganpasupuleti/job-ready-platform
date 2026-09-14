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
  { label: 'Playground', path: '/practice/python', match: ['/practice/python', '/practice/playground'] },
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
      { label: 'Playground', path: '/practice/python', icon: 'Terminal' },
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

/** Grouped More menu. Existing routes stay; this is layout, not a new destination set. */
export const moreMenuGroups: { title: string; items: { label: string; path: string }[] }[] = [
  {
    title: 'Practice',
    items: [
      { label: 'SQL', path: '/practice/sql' },
      { label: 'DSA', path: '/practice/dsa' },
      { label: 'Coding', path: '/practice/coding' },
      { label: 'Technical MCQs', path: '/practice/mcq' },
      { label: 'Aptitude / CRT', path: '/practice/aptitude' },
    ],
  },
  {
    title: 'Career',
    items: [
      { label: 'Projects', path: '/practice/projects' },
      { label: 'Job Readiness', path: '/readiness' },
      { label: 'Interview Prep', path: '/interviews' },
      { label: 'Bookmarks', path: '/bookmarks' },
      { label: 'Recommended Jobs', path: '/jobs/recommended' },
      { label: 'Applications', path: '/jobs/applications' },
    ],
  },
  {
    title: 'AI & Engineering',
    items: [
      { label: 'AI Home', path: '/ai' },
      { label: 'Prompt Engineering', path: '/ai/prompt-engineering' },
      { label: 'Cloud', path: '/cloud' },
      { label: 'DevOps', path: '/devops' },
      { label: 'Cybersecurity', path: '/cybersecurity' },
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

function matchingPrefix(pathname: string, item: (typeof primaryNavItems)[number]) {
  const matchers = item.match ?? [item.path]
  let best = ''
  for (const prefix of matchers) {
    const hit =
      prefix === '/'
        ? pathname === '/'
        : pathname === prefix || pathname.startsWith(`${prefix}/`)
    if (hit && prefix.length > best.length) best = prefix
  }
  return best
}

/** Longest matching destination wins, so only one primary item is current. */
export function isPrimaryNavActive(pathname: string, item: (typeof primaryNavItems)[number]) {
  const ranked = primaryNavItems
    .map((candidate) => ({ candidate, prefix: matchingPrefix(pathname, candidate) }))
    .filter((row) => row.prefix.length > 0)
    .sort((left, right) => right.prefix.length - left.prefix.length)
  return ranked[0]?.candidate === item
}
