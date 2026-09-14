import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { LearnSubnav } from '@/components/learn/LearnSubnav'
import { fetchStudioCatalog } from '@/services/studioService'

export function MaterialsPage() {
  const [params, setParams] = useSearchParams()
  const family = params.get('family') ?? ''
  const skill = params.get('skill') ?? ''
  const level = params.get('level') ?? ''
  const kind = params.get('kind') ?? ''
  const progress = params.get('progress') ?? ''
  const query = Object.fromEntries(
    Object.entries({ family, skill, level, kind, progress }).filter(([, value]) => value),
  )
  const { data, isLoading, isError } = useQuery({
    queryKey: ['studio-catalog', query],
    queryFn: () => fetchStudioCatalog(query),
  })

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next)
  }

  return (
    <div className="module-page learn-page">
      <LearnSubnav />
      <header className="module-heading">
        <div>
          <p className="eyebrow">Learn</p>
          <h1>Materials</h1>
          <p>Published articles and cheat sheets. Marking an item read is not a grade.</p>
        </div>
      </header>
      <div className="mb-4 flex flex-wrap gap-2">
        <Filter label="Family" value={family} onChange={(value) => setFilter('family', value)} options={(data?.families ?? []).map((item) => ({ value: item.id, label: `${item.label} (${item.count})` }))} />
        <Filter label="Skill" value={skill} onChange={(value) => setFilter('skill', value)} options={(data?.skills ?? []).map((item) => ({ value: item.id, label: `${item.id} (${item.count})` }))} />
        <Filter label="Level" value={level} onChange={(value) => setFilter('level', value)} options={(data?.levels ?? []).map((item) => ({ value: item.id, label: `${item.id} (${item.count})` }))} />
        <Filter label="Type" value={kind} onChange={(value) => setFilter('kind', value)} options={(data?.kinds ?? []).map((item) => ({ value: item.id, label: `${item.id} (${item.count})` }))} />
        <Filter
          label="Progress"
          value={progress}
          onChange={(value) => setFilter('progress', value)}
          options={[
            { value: 'latest', label: 'Latest' },
            { value: 'in_progress', label: 'In progress' },
          ]}
        />
      </div>
      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading materials...</p>
      ) : isError ? (
        <p className="text-sm text-[var(--color-danger)]" role="alert">Unable to load materials.</p>
      ) : (data?.materials.length ?? 0) === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">No published materials match these filters.</p>
      ) : (
        <div className="course-grid">
          {data!.materials.map((item) => (
            <Link key={item.key} to={`/learn/materials/${item.key}`} className="course-tile">
              <strong>{item.title}</strong>
              <p>{item.kind} · {item.level} · {item.minutes} min</p>
              <span>{item.read ? 'Marked read' : 'Not marked read'}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

function Filter({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
}) {
  const id = `filter-${label.toLowerCase()}`
  return (
    <label className="text-sm" htmlFor={id}>
      <span className="mr-1 text-[var(--color-text-muted)]">{label}</span>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)} className="rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1">
        <option value="">Any</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  )
}
