/**
 * Mock data for Build 1 development.
 * Remove or replace with real API data in later builds.
 */

import type { DashboardCard, UpcomingAssessment, WeakSkill } from '@/types'

export const mockDashboardCards: DashboardCard[] = [
  {
    id: 'readiness',
    title: 'Job Readiness Score',
    value: '72%',
    subtitle: 'Target: 85%',
    trend: '+4% this week',
    trendDirection: 'up',
  },
  {
    id: 'today-practice',
    title: "Today's Practice",
    value: '45 min',
    subtitle: 'Goal: 60 min',
    trend: '3 sessions completed',
    trendDirection: 'neutral',
  },
  {
    id: 'coding-progress',
    title: 'Coding Progress',
    value: '28 / 120',
    subtitle: 'problems solved',
    trend: '+2 this week',
    trendDirection: 'up',
  },
  {
    id: 'aptitude-progress',
    title: 'Aptitude Progress',
    value: '64%',
    subtitle: 'CRT modules',
    trend: '+6% this month',
    trendDirection: 'up',
  },
  {
    id: 'interview-readiness',
    title: 'Interview Readiness',
    value: 'Moderate',
    subtitle: 'Based on mock interviews',
    trend: '2 mocks pending review',
    trendDirection: 'neutral',
  },
  {
    id: 'recommended-jobs',
    title: 'Recommended Jobs',
    value: '12',
    subtitle: 'matching your profile',
    trend: '3 new today',
    trendDirection: 'up',
  },
  {
    id: 'streak',
    title: 'Current Streak',
    value: '7 days',
    subtitle: 'Personal best: 14 days',
    trend: 'Keep it going!',
    trendDirection: 'up',
  },
]

export const mockWeakSkills: WeakSkill[] = [
  { skill: 'Dynamic Programming', score: 42 },
  { skill: 'System Design', score: 48 },
  { skill: 'SQL Joins', score: 55 },
  { skill: 'Probability', score: 58 },
]

export const mockUpcomingAssessments: UpcomingAssessment[] = [
  {
    id: '1',
    title: 'DSA Weekly Challenge',
    date: 'Sep 2, 2026',
    type: 'Contest',
  },
  {
    id: '2',
    title: 'Aptitude Mock Test #4',
    date: 'Sep 5, 2026',
    type: 'Assessment',
  },
  {
    id: '3',
    title: 'SQL Fundamentals Quiz',
    date: 'Sep 8, 2026',
    type: 'Quiz',
  },
]
