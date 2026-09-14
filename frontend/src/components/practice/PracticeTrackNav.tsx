import { NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { fetchCodingProgress } from '@/services/codingService'
import { fetchCatalog } from '@/services/practiceService'
import { fetchSqlProgress } from '@/services/sqlService'
import type { DomainBrief } from '@/types/practice'

function countTopics(domains: DomainBrief[] | undefined, domainSlug: string, categorySlug?: string) {
  const domain = domains?.find((item) => item.slug === domainSlug)
  if (!domain) return null
  const categories = categorySlug
    ? domain.categories.filter((category) => category.slug === categorySlug)
    : domain.categories
  if (!categories.length) return null
  return categories.reduce((total, category) => total + category.topics.length, 0)
}

/** Cross-track jumps using catalog, coding progress, and SQL progress — no new API. */
export function PracticeTrackNav() {
  const catalog = useQuery({
    queryKey: ['practice-catalog'],
    queryFn: fetchCatalog,
  })
  const coding = useQuery({
    queryKey: ['coding-progress'],
    queryFn: fetchCodingProgress,
  })
  const sql = useQuery({
    queryKey: ['sql-progress'],
    queryFn: fetchSqlProgress,
  })

  const tracks: { label: string; to: string; end?: boolean; count: string | number | null }[] = [
    { label: 'Practice', to: '/practice', end: true, count: null },
    {
      label: 'Aptitude',
      to: '/practice/aptitude',
      count: countTopics(catalog.data?.domains, 'placement', 'aptitude'),
    },
    { label: 'MCQ', to: '/practice/mcq', count: countTopics(catalog.data?.domains, 'technical') },
    {
      label: 'DSA',
      to: '/practice/dsa',
      count:
        coding.data != null ? `${coding.data.solved_count}/${coding.data.total_problems}` : null,
    },
    {
      label: 'SQL',
      to: '/practice/sql',
      count: sql.data != null ? `${sql.data.solved_count}/${sql.data.total_problems}` : null,
    },
  ]

  return (
    <nav className="practice-track-nav" aria-label="Practice tracks">
      {tracks.map((track) => (
        <NavLink
          key={track.to}
          to={track.to}
          end={track.end}
          className={({ isActive }) => `practice-track-link${isActive ? ' is-active' : ''}`}
        >
          {track.label}
          {track.count != null ? <span className="practice-track-count">{track.count}</span> : null}
        </NavLink>
      ))}
    </nav>
  )
}
