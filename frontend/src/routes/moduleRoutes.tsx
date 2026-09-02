import type { LucideIcon } from 'lucide-react'
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
  ListChecks,
  MessageSquare,
  Shield,
  Sparkles,
  Target,
  Terminal,
  Trophy,
  Users,
  Wrench,
} from 'lucide-react'

export interface ModuleRouteConfig {
  path: string
  title: string
  description: string
  icon: LucideIcon
}

export const moduleRoutes: ModuleRouteConfig[] = [
  {
    path: 'practice/aptitude',
    title: 'Aptitude / CRT',
    description:
      'Quantitative aptitude, logical reasoning, and campus recruitment test preparation.',
    icon: Brain,
  },
  {
    path: 'practice/dsa',
    title: 'DSA Practice',
    description: 'Data structures and algorithms problems with difficulty tracking and progress.',
    icon: Code2,
  },
  {
    path: 'practice/coding',
    title: 'Coding Practice',
    description: 'Hands-on coding challenges with editor, submissions, and test case feedback.',
    icon: Terminal,
  },
  {
    path: 'practice/sql',
    title: 'SQL Practice',
    description: 'Query writing exercises across joins, aggregations, window functions, and more.',
    icon: Database,
  },
  {
    path: 'practice/mcq',
    title: 'Technical MCQs',
    description: 'Multiple-choice assessments covering core computer science and engineering topics.',
    icon: FileQuestion,
  },
  {
    path: 'ai/ml',
    title: 'AI / ML',
    description: 'Machine learning fundamentals, model concepts, and applied AI knowledge tracks.',
    icon: Sparkles,
  },
  {
    path: 'ai/genai',
    title: 'Generative AI',
    description: 'LLM concepts, use cases, safety, and practical generative AI workflows.',
    icon: Bot,
  },
  {
    path: 'ai/prompt-engineering',
    title: 'Prompt Engineering',
    description: 'Structured prompting, evaluation patterns, and prompt optimization exercises.',
    icon: MessageSquare,
  },
  {
    path: 'ai/agents',
    title: 'AI Agents',
    description: 'Agent architectures, tool use, orchestration, and autonomous workflow design.',
    icon: Users,
  },
  {
    path: 'cloud',
    title: 'Cloud',
    description: 'Cloud platforms, services, architecture patterns, and certification prep.',
    icon: Cloud,
  },
  {
    path: 'devops',
    title: 'DevOps',
    description: 'CI/CD, containers, infrastructure as code, and operational best practices.',
    icon: Wrench,
  },
  {
    path: 'cybersecurity',
    title: 'Cybersecurity',
    description: 'Security fundamentals, threat modeling, and defensive engineering concepts.',
    icon: Shield,
  },
  {
    path: 'interviews',
    title: 'Interview Preparation',
    description: 'Mock interviews, theory questions, coding rounds, and structured feedback.',
    icon: Users,
  },
  {
    path: 'company-prep',
    title: 'Company-specific Preparation',
    description: 'Targeted preparation paths for specific companies and role requirements.',
    icon: Building2,
  },
  {
    path: 'assessments',
    title: 'Assessments',
    description: 'Timed assessments combining MCQs, coding, and domain-specific evaluations.',
    icon: ListChecks,
  },
  {
    path: 'contests',
    title: 'Contests',
    description: 'Competitive programming and hiring-style contests with live leaderboards.',
    icon: Trophy,
  },
  {
    path: 'jobs',
    title: 'Browse Jobs',
    description: 'Explore job listings with filters for role, location, experience, and skills.',
    icon: Briefcase,
  },
  {
    path: 'jobs/recommended',
    title: 'Recommended Jobs',
    description: 'Personalized job recommendations based on your readiness profile and skills.',
    icon: Target,
  },
  {
    path: 'jobs/saved',
    title: 'Saved Jobs',
    description: 'Jobs you have bookmarked for later review and application.',
    icon: Bookmark,
  },
  {
    path: 'jobs/applications',
    title: 'Applications',
    description: 'Track application status, interview stages, and follow-up actions.',
    icon: Award,
  },
  {
    path: 'bookmarks',
    title: 'Bookmarks',
    description: 'Saved problems, articles, and resources across all learning modules.',
    icon: Bookmark,
  },
  {
    path: 'leaderboard',
    title: 'Leaderboard',
    description: 'Community rankings by practice streaks, contest performance, and readiness.',
    icon: Flame,
  },
]
