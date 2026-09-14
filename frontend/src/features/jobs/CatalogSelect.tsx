import { useEffect, useId, useRef, useState } from 'react'

export function CatalogSelect({
  label,
  value,
  options,
  loading,
  error,
  onQueryChange,
  onChange,
}: {
  label: string
  value: string
  options: string[]
  loading: boolean
  error: boolean
  onQueryChange: (query: string) => void
  onChange: (value: string) => void
}) {
  const listId = useId()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState(value)
  const [active, setActive] = useState(0)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setQuery(value)
  }, [value])

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [])

  const choose = (next: string) => {
    onChange(next)
    setQuery(next)
    setOpen(false)
  }

  return (
    <div className="jobs-catalog-select" ref={rootRef}>
      <input
        className="jobs-catalog-input"
        role="combobox"
        aria-label={label}
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        placeholder={label}
        value={query}
        onFocus={() => {
          setOpen(true)
          onQueryChange(query)
        }}
        onChange={(event) => {
          setQuery(event.target.value)
          setOpen(true)
          setActive(0)
          onQueryChange(event.target.value)
        }}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown') {
            event.preventDefault()
            setOpen(true)
            setActive((current) => Math.min(current + 1, Math.max(options.length - 1, 0)))
          } else if (event.key === 'ArrowUp') {
            event.preventDefault()
            setActive((current) => Math.max(current - 1, 0))
          } else if (event.key === 'Enter' && open && options[active]) {
            event.preventDefault()
            choose(options[active])
          } else if (event.key === 'Escape') {
            setOpen(false)
            setQuery(value)
          }
        }}
      />
      {open && (
        <ul className="jobs-catalog-list" id={listId} role="listbox" aria-label={label}>
          {loading ? (
            <li className="jobs-catalog-status">Loading options</li>
          ) : error ? (
            <li className="jobs-catalog-status">Unable to load options</li>
          ) : options.length === 0 ? (
            <li className="jobs-catalog-status">No matches</li>
          ) : (
            options.map((option, index) => (
              <li key={option} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={option === value || index === active}
                  className={index === active ? 'is-active' : undefined}
                  onMouseEnter={() => setActive(index)}
                  onClick={() => choose(option)}
                >
                  {option}
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  )
}
