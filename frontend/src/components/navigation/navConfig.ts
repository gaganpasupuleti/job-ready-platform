import type { ComponentType } from 'react'
import {
  Award,
  BookOpen,
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

/** Primary horizontal nav. Coding stays on the existing practice route. */
export const primaryNavItems: { label: string; path: string; match?: string[] }[] = [
  { label: 'Jobs', path: '/jobs', match: ['/jobs'] },
  { label: 'Overview', path: '/', match: ['/'] },
  { label: 'Practice', path: '/practice', match: ['/practice'] },
  { label: 'Learn', path: '/learn', match: ['/learn', '/projects', '/practice/projects'] },
  { label: 'Coding', path: '/practice/coding', match: ['/practice/coding', '/practice/dsa'] },
  {
    label: 'Assessments',
    path: '/practice/aptitude',
    match: ['/practice/aptitude', '/practice/mcq', '/practice/sessions'],
  },
  { label: 'Review', path: '/mistakes', match: ['/mistakes'] },
]

export const navigationConfig: NavSection[] = [
  {
    title: 'Main',
    items: [{ label: 'Dashboard', path: '/', icon: 'LayoutDashboard' }],
  },
  {
    title: 'Practice',
    items: [
      { label: 'Practice Hub', path: '/practice', icon: 'Target' },
      { label: 'Courses', path: '/learn', icon: 'ListChecks' },
      { label: 'Projects', path: '/practice/projects', icon: 'Wrench' },
      { label: 'Aptitude / CRT', path: '/practice/aptitude', icon: 'Brain' },
      { label: 'DSA', path: '/practice/dsa', icon: 'Code2' },
      { label: 'Coding', path: '/practice/coding', icon: 'Terminal' },
      { label: 'SQL', path: '/practice/sql', icon: 'Database' },
      { label: 'Technical MCQs', path: '/practice/mcq', icon: 'FileQuestion' },
    ],
  },
  {
    title: 'AI Era',
    items: [
      { label: 'AI Home', path: '/ai', icon: 'Sparkles' },
      { label: 'Generative AI', path: '/ai/genai', icon: 'Bot' },
      { label: 'Prompt Engineering', path: '/ai/prompt-engineering', icon: 'MessageSquare' },
      { label: 'RAG', path: '/ai/rag', icon: 'Database' },
      { label: 'AI Agents', path: '/ai/agents', icon: 'Users' },
      { label: 'MCP', path: '/ai/mcp', icon: 'Server' },
      { label: 'AI Progress', path: '/ai/progress', icon: 'Target' },
    ],
  },
  {
    title: 'Infrastructure',
    items: [
      { label: 'Cloud', path: '/cloud', icon: 'Cloud' },
      { label: 'DevOps', path: '/devops', icon: 'Wrench' },
      { label: 'Cybersecurity', path: '/cybersecurity', icon: 'Shield' },
    ],
  },
  {
    title: 'Career',
    items: [
      { label: 'Interview Prep', path: '/interviews', icon: 'Users' },
      { label: 'Company Prep', path: '/company-prep', icon: 'Building2' },
      { label: 'Assessments', path: '/assessments', icon: 'ListChecks' },
      { label: 'Contests', path: '/contests', icon: 'Trophy' },
    ],
  },
  {
    title: 'Jobs',
    items: [
      { label: 'Browse Jobs', path: '/jobs', icon: 'Briefcase' },
      { label: 'Recommended Jobs', path: '/jobs/recommended', icon: 'Target' },
      { label: 'Saved Jobs', path: '/jobs/saved', icon: 'Bookmark' },
      { label: 'Applications', path: '/jobs/applications', icon: 'Award' },
    ],
  },
  {
    title: 'Progress',
    items: [
      { label: 'Job Readiness', path: '/readiness', icon: 'Target' },
      { label: 'Library', path: '/library', icon: 'BookOpen' },
      { label: 'Mistake Book', path: '/mistakes', icon: 'FileQuestion' },
      { label: 'Bookmarks', path: '/bookmarks', icon: 'Bookmark' },
      { label: 'Leaderboard', path: '/leaderboard', icon: 'Flame' },
    ],
  },
]

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
  BookOpen,
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
