import type { RefObject } from 'react'
import { Link } from 'react-router-dom'

import { cn } from '@/utils/cn'

import type { RoadmapAssembly, RoadmapNode } from '../types'
import { orderedPhases } from '../adapter'
import { resolveResourceDestination, resourceActionLabel } from '../destinations'
import {
  availabilityPlain,
  importancePlain,
  phaseLabel,
  proofStatusPlain,
  reasonCodePlain,
  resourceAvailabilityPlain,
} from '../labels'

interface RoadmapListProps {
  assembly: RoadmapAssembly
  selectedKey: string | null
  startHereKey: string | null
  onSelect: (nodeKey: string) => void
}

export function RoadmapList({ assembly, selectedKey, startHereKey, onSelect }: RoadmapListProps) {
  const byKey = new Map(assembly.nodes.map((n) => [n.node_key, n]))
  const phases = orderedPhases(assembly)

  return (
    <div className="rm-list" role="list">
      {phases.map((phase) => (
        <section key={phase.phase_key} className="rm-list-phase" aria-labelledby={`phase-${phase.phase_key}`}>
          <h2 id={`phase-${phase.phase_key}`} className="rm-list-phase__title">
            {phaseLabel(phase.phase_key)}
          </h2>
          <ul className="rm-list-phase__items">
            {phase.node_keys
              .slice()
              .sort(
                (a, b) =>
                  (byKey.get(a)?.planned_index ?? 0) - (byKey.get(b)?.planned_index ?? 0),
              )
              .map((key) => {
                const node = byKey.get(key)
                if (!node) return null
                return (
                  <li key={key}>
                    <button
                      type="button"
                      role="listitem"
                      className={cn(
                        'rm-list-item',
                        selectedKey === key && 'rm-list-item--selected',
                        node.node_key === startHereKey && 'rm-list-item--start',
                      )}
                      aria-pressed={selectedKey === key}
                      onClick={() => onSelect(key)}
                    >
                      <span className="rm-list-item__title">
                        {node.title}
                        {node.node_key === startHereKey ? (
                          <span className="rm-inline-start">Start here</span>
                        ) : null}
                      </span>
                      <span className="rm-list-item__meta">
                        {importancePlain(node.importance, node.is_optional)} ·{' '}
                        {availabilityPlain(node.availability)}
                      </span>
                    </button>
                  </li>
                )
              })}
          </ul>
        </section>
      ))}
    </div>
  )
}

interface DetailsPanelProps {
  node: RoadmapNode | null
  assembly: RoadmapAssembly
  onClose: () => void
  panelRef: RefObject<HTMLElement | null>
}

export function RoadmapDetailsPanel({ node, assembly, onClose, panelRef }: DetailsPanelProps) {
  if (!node) {
    return (
      <aside className="rm-details rm-details--empty" aria-label="Node details" ref={panelRef}>
        <p className="text-sm text-[var(--color-text-muted)]">
          Select a node to see status, prerequisites, and learning actions.
        </p>
      </aside>
    )
  }

  const titleMap = new Map(assembly.nodes.map((n) => [n.node_key, n.title]))

  return (
    <aside
      className="rm-details"
      aria-label={`Details for ${node.title}`}
      ref={panelRef}
      tabIndex={-1}
    >
      <div className="rm-details__head">
        <div>
          <p className="rm-details__eyebrow">{phaseLabel(node.phase_key)}</p>
          <h2 className="rm-details__title">{node.title}</h2>
        </div>
        <button type="button" className="rm-btn rm-btn--ghost" onClick={onClose} aria-label="Close details">
          Close
        </button>
      </div>

      <dl className="rm-details__facts">
        <div>
          <dt>Requirement</dt>
          <dd>{importancePlain(node.importance, node.is_optional)}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{availabilityPlain(node.availability)}</dd>
        </div>
        <div>
          <dt>Proof</dt>
          <dd>{proofStatusPlain(node.proof_status)}</dd>
        </div>
        <div>
          <dt>Planned order</dt>
          <dd>
            #{node.planned_index + 1} in sequence (not completion)
          </dd>
        </div>
      </dl>

      {node.availability_reason_codes.length > 0 ? (
        <section className="rm-details__section">
          <h3>Why this status</h3>
          <ul>
            {node.availability_reason_codes.map((c) => (
              <li key={c}>{reasonCodePlain(c)}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="rm-details__section">
        <h3>Hard prerequisites</h3>
        {node.hard_prerequisite_node_keys.length === 0 ? (
          <p className="rm-muted">None — this node has no hard prerequisite edges.</p>
        ) : (
          <ul>
            {node.hard_prerequisite_node_keys.map((k) => {
              const unsatisfied = node.unsatisfied_hard_prerequisite_node_keys.includes(k)
              return (
                <li key={k}>
                  {titleMap.get(k) ?? k}
                  {unsatisfied ? ' — not established' : ' — established (per backend)'}
                </li>
              )
            })}
          </ul>
        )}
      </section>

      <section className="rm-details__section">
        <h3>Learning actions</h3>
        {node.resources.length === 0 ? (
          <p className="rm-muted">No resources linked — content incomplete for this node.</p>
        ) : (
          <ul className="rm-actions">
            {node.resources.map((r) => {
              const dest = resolveResourceDestination(r, node)
              const lockedExec =
                r.availability === 'execution_unavailable' ||
                r.reason_codes.includes('judge0_disabled')
              return (
                <li key={`${r.type}:${r.ref}`} className="rm-action">
                  <div>
                    <p className="rm-action__label">
                      {resourceActionLabel(r.type)} · {r.ref}
                    </p>
                    <p className="rm-action__status">
                      {resourceAvailabilityPlain(r.availability)}
                      {r.reason_codes.length
                        ? ` (${r.reason_codes.map(reasonCodePlain).join(', ')})`
                        : ''}
                    </p>
                    {dest.note ? <p className="rm-action__note">{dest.note}</p> : null}
                    {lockedExec ? (
                      <p className="rm-action__note">
                        Run/Submit remains locked. Theory links may still open when available.
                      </p>
                    ) : null}
                  </div>
                  {dest.resolvable && dest.href && r.availability === 'available' ? (
                    <Link className="rm-btn rm-btn--accent" to={dest.href}>
                      {dest.label}
                    </Link>
                  ) : r.availability === 'missing' || r.availability === 'unpublished_or_inaccessible' ? (
                    <span className="rm-chip rm-chip--warn">Missing / inaccessible</span>
                  ) : (
                    <span className="rm-chip">Unresolved destination</span>
                  )}
                </li>
              )
            })}
          </ul>
        )}
        <p className="rm-muted rm-details__footnote">
          Opening a resource does not mark this roadmap node complete.
        </p>
      </section>
    </aside>
  )
}
