import { marked } from 'marked'

import { Button } from '@/components/common/Button'
import { sanitizeArticleHtml } from '@/lib/sanitizeHtml'
import type { OfficialRoadmapNode } from '@/services/roadmapOfficialService'

import { rewriteRoadmapShMarkdown } from './roadmapShLinks'

interface RoadmapTopicPanelProps {
  selected: OfficialRoadmapNode | null
  topicMarkdown?: string
  topicAttribution?: string
  isLoading: boolean
  errorKind: 'none' | 'missing' | 'network' | 'session'
  allowedSlugs?: ReadonlySet<string>
  onRetry?: () => void
  onClose?: () => void
  closeButtonDataAttr?: boolean
}

function topicErrorMessage(kind: RoadmapTopicPanelProps['errorKind']): string | null {
  switch (kind) {
    case 'missing':
      return 'This topic does not have a reading article yet. The map still shows how it fits the path.'
    case 'network':
      return 'We could not load this topic right now.'
    case 'session':
      return 'Sign in again to load topic articles.'
    case 'none':
      return null
    default: {
      const _exhaustive: never = kind
      return _exhaustive
    }
  }
}

export function RoadmapTopicPanel({
  selected,
  topicMarkdown,
  topicAttribution,
  isLoading,
  errorKind,
  allowedSlugs,
  onRetry,
  onClose,
  closeButtonDataAttr,
}: RoadmapTopicPanelProps) {
  if (!selected) {
    return null
  }

  const html = topicMarkdown
    ? sanitizeArticleHtml(
        marked.parse(rewriteRoadmapShMarkdown(topicMarkdown, allowedSlugs), { async: false }) as string,
      )
    : ''

  const errorMessage = topicErrorMessage(errorKind)

  return (
    <div className="ors-topic-panel">
      <div className="ors-topic-panel-head">
        <h2 className="ors-panel-title">{selected.data?.label ?? 'Topic'}</h2>
        {onClose ? (
          <button
            type="button"
            className="ors-topic-close"
            onClick={onClose}
            {...(closeButtonDataAttr ? { 'data-topic-dialog-close': true } : {})}
          >
            Close
          </button>
        ) : null}
      </div>
      {isLoading ? <p className="ors-muted">Loading topic…</p> : null}
      {errorMessage ? (
        <div className="ors-topic-error" role="status">
          <p className="ors-muted">{errorMessage}</p>
          {onRetry && (errorKind === 'network' || errorKind === 'session') ? (
            <Button type="button" size="sm" variant="secondary" onClick={onRetry}>
              Retry
            </Button>
          ) : null}
        </div>
      ) : null}
      {html ? (
        <>
          <article
            className="ors-markdown prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: html }}
          />
          {topicAttribution ? <p className="ors-attribution">{topicAttribution}</p> : null}
        </>
      ) : null}
    </div>
  )
}
