import { Link, useLocation } from 'react-router-dom'

const items = [
  { label: 'Courses', path: '/learn' },
  { label: 'Syllabus', path: '/learn/syllabus' },
  { label: 'Materials', path: '/learn/materials' },
  { label: 'Assignments', path: '/learn/assignments' },
  { label: 'Projects', path: '/practice/projects' },
]

export function LearnSubnav() {
  const { pathname } = useLocation()
  return (
    <nav className="mb-4 flex flex-wrap gap-2" aria-label="Learn">
      {items.map((item) => {
        const active = item.path === '/learn' ? pathname === '/learn' || pathname.startsWith('/learn/courses') : pathname.startsWith(item.path)
        return (
          <Link
            key={item.path}
            to={item.path}
            aria-current={active ? 'page' : undefined}
            className={
              active
                ? 'rounded-[5px] border border-[var(--color-accent)] px-3 py-1 text-sm text-[var(--color-text)]'
                : 'rounded-[5px] border border-[var(--color-border)] px-3 py-1 text-sm text-[var(--color-text-muted)]'
            }
          >
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}
