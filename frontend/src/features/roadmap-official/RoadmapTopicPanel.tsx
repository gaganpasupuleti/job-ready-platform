import { marked } from 'marked'

import { sanitizeArticleHtml } from '@/lib/sanitizeHtml'
import type { OfficialRoadmapNode } from '@/services/roadmapOfficialService'

import { rewriteRoadmapShMarkdown } from './roadmapShLinks'

interface RoadmapTopicPanelProps {
  selected: OfficialRoadmapNode | null
  topicMarkdown?: string
  topicAttribution?: string
  isLoading: boolean
  errorKind: 'none' | 'missing' | 'network' | 'session'
  onClose?: () => void
}

function topicErrorMessage(kind: RoadmapTopicPanelProps['errorKind']): string | null {
  switch (kind) {
    case 'missing':
      return 'This topic does not have a reading article yet. The map still shows how it fits the path.'
    case 'network':
      return 'We could not load this topic right now. Try again in a moment.'
    case 'session':
      return 'Sign in again to load topic articles.'
    case 'none':
      return null
    default:
      return null
  }
}

export function RoadmapTopicPanel({
  selected,
  topicMarkdown,
  topicAttribution,
  isLoading,
  errorKind,
  onClose,
}: RoadmapTopicPanelProps) {
  if (!selected) {
    return (
      <p className="ors-panel-empty">
        Select a topic on the map or in the outline to read notes here.
      </p>
    )
  }

  const html = topicMarkdown
    ? sanitizeArticleHtml(
        marked.parse(rewriteRoadmapShMarkdown(topicMarkdown), { async: false }) as string,
      )
    : ''

  const errorMessage = topicErrorMessage(errorKind)

  return (
    <div className="ors-topic-panel">
      <div className="ors-topic-panel-head">
        <h2 className="ors-panel-title">{selected.data?.label ?? 'Topic'}</h2>
        {onClose ? (
          <button type="button" className="ors-topic-close" onClick={onClose}>
            Close
          </button>
        ) : null}
      </div>
      {isLoading ? <p className="text-sm">Loading topic…</p> : null}
      {errorMessage ? (
        <p className="text-sm text-[var(--color-text-muted)]" role="status">{errorMessage}</p>
      ) : null}
      {html ? (
        <>
          <article
            className="ors-markdown prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: html }}
          />
          {topicAttribution ? (
            <p className="ors-attribution text-xs text-[var(--color-text-subtle)]">{topicAttribution}</p>
          ) : null}
        </>
      ) : null}
    </div>
  )
}
