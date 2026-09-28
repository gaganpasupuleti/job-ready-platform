import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { LearnSubnav } from '@/components/learn/LearnSubnav'
import { fetchSyllabusTracks } from '@/services/studioService'

export function SyllabusPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['studio-syllabus'],
    queryFn: fetchSyllabusTracks,
  })

  return (
    <div className="module-page learn-page">
      <LearnSubnav />
      <header className="module-heading">
        <div>
          <p className="eyebrow">Learn</p>
          <h1>Syllabus</h1>
          <p>
            Placement preparation (CRT / Aptitude) and DSA Foundations. Published lessons open as
            full articles. Unwritten topics stay Coming soon.
          </p>
        </div>
      </header>
      {isLoading ? (
        <p>Loading syllabus...</p>
      ) : isError || !data ? (
        <p role="alert">Unable to load the syllabus.</p>
      ) : (
        <div className="space-y-8">
          {data.tracks.map((track) => (
            <section key={track.id}>
              <h2 className="text-base font-semibold">{track.title}</h2>
              <div className="mt-3 space-y-4">
                {track.units.map((unit) => (
                  <div key={unit.id} className="rounded-[5px] border border-[var(--color-border)] p-3">
                    <h3 className="text-sm font-semibold">{unit.title}</h3>
                    <ol className="mt-2 space-y-2">
                      {unit.lessons.map((lesson) => (
                        <li key={lesson.key} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                          <span>
                            {lesson.position}. {lesson.title}
                            {lesson.minutes ? ` · ${lesson.minutes} min` : ''}
                          </span>
                          {lesson.status === 'published' && lesson.href ? (
                            <Link
                              to={`/learn/syllabus/${lesson.key}`}
                              className="text-[var(--color-accent)] hover:underline"
                            >
                              Open lesson
                            </Link>
                          ) : (
                            <span className="text-[var(--color-text-muted)]">Coming soon</span>
                          )}
                        </li>
                      ))}
                    </ol>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
