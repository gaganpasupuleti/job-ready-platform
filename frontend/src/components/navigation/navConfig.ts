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
      { label: 'AI / ML', path: '/ai/ml', icon: 'Sparkles' },
      { label: 'Generative AI', path: '/ai/genai', icon: 'Bot' },
      { label: 'Prompt Engineering', path: '/ai/prompt-engineering', icon: 'MessageSquare' },
      { label: 'AI Agents', path: '/ai/agents', icon: 'Users' },
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
  Award,
  Flame,
  Server,
}

export function getNavIcon(name?: string) {
  if (!name) return LayoutDashboard
  return iconMap[name] ?? LayoutDashboard
}
