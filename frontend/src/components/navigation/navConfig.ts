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

/** Primary student destinations (Sprint 1 shell). Deep links stay in More. */
export const navigationConfig: NavSection[] = [
  {
    title: 'Today',
    items: [
      { label: 'Dashboard', path: '/', icon: 'LayoutDashboard' },
      { label: 'Practice', path: '/practice', icon: 'Target' },
      { label: 'Learn', path: '/learn', icon: 'ListChecks' },
      { label: 'Mistakes', path: '/mistakes', icon: 'FileQuestion' },
      { label: 'Jobs', path: '/jobs', icon: 'Briefcase' },
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
