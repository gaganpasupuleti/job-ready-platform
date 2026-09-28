import { Link, useLocation } from 'react-router-dom'

interface PracticeDestination {
  label: string
  to: string
  match: string[]
}

/** Destination navigation only. Topic and difficulty filters stay on the page. */
const destinations: PracticeDestination[] = [
  { label: 'Typing', to: '/practice/typing', match: ['/practice/typing'] },
  { label: 'Aptitude & Reasoning', to: '/practice/aptitude', match: ['/practice/aptitude'] },
  { label: 'SQL', to: '/practice/sql', match: ['/practice/sql'] },
  {
    label: 'Programming & DSA',
    to: '/practice/dsa',
    match: ['/practice/dsa', '/practice/coding'],
  },
  { label: 'Quizzes', to: '/practice/mcq', match: ['/practice/mcq'] },
  { label: 'Projects', to: '/practice/projects', match: ['/practice/projects'] },
]

function isDestinationActive(pathname: string, match: string[]) {
  return match.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))
}

export function PracticeTrackNav() {
  const { pathname } = useLocation()

  return (
    <nav className="practice-track-nav" aria-label="Practice destinations">
      {destinations.map((item) => {
        const active = isDestinationActive(pathname, item.match)
        return (
          <Link
            key={item.to}
            to={item.to}
            className={`practice-track-link${active ? ' is-active' : ''}`}
            aria-current={active ? 'page' : undefined}
          >
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}
