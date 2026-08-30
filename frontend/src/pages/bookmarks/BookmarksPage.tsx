import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import { CodingProblemList } from '@/features/dsa/CodingProblemList'
import { SqlProblemList } from '@/features/sql/SqlProblemList'
import { fetchPromptBookmarks } from '@/services/aiService'
import { fetchCodingBookmarks } from '@/services/codingService'
import { fetchPracticeBookmarks } from '@/services/practiceService'
import { fetchSqlBookmarks } from '@/services/sqlService'

type Tab = 'mcq' | 'coding' | 'sql' | 'prompt'

export function BookmarksPage() {
  const [tab, setTab] = useState<Tab>('mcq')

  const { data: mcqBookmarks, isLoading: mcqLoading } = useQuery({
    queryKey: ['mcq-bookmarks'],
    queryFn: fetchPracticeBookmarks,
    enabled: tab === 'mcq',
  })

  const { data: codingBookmarks, isLoading: codingLoading } = useQuery({
    queryKey: ['coding-bookmarks'],
    queryFn: fetchCodingBookmarks,
    enabled: tab === 'coding',
  })

  const { data: sqlBookmarks, isLoading: sqlLoading } = useQuery({
    queryKey: ['sql-bookmarks'],
    queryFn: fetchSqlBookmarks,
    enabled: tab === 'sql',
  })

  const { data: promptBookmarks, isLoading: promptLoading } = useQuery({
    queryKey: ['prompt-bookmarks'],
    queryFn: fetchPromptBookmarks,
    enabled: tab === 'prompt',
  })

  const tabLabel: Record<Tab, string> = {
    mcq: 'MCQ Questions',
    coding: 'Coding Problems',
    sql: 'SQL Problems',
    prompt: 'Prompt Challenges',
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Bookmarks</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Saved MCQ questions, coding problems, SQL problems, and prompt challenges.
        </p>
      </div>

      <div className="flex gap-2 border-b border-[var(--color-border)]">
        {(['mcq', 'coding', 'sql', 'prompt'] as Tab[]).map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`border-b-2 px-3 py-2 text-sm ${
              tab === key
                ? 'border-[var(--color-accent)] text-[var(--color-accent)]'
                : 'border-transparent text-[var(--color-text-muted)]'
            }`}
          >
            {tabLabel[key]}
          </button>
        ))}
      </div>

      {tab === 'mcq' && (
        <Card>
          <CardHeader title={`MCQ bookmarks (${mcqBookmarks?.length ?? 0})`} />
          {mcqLoading ? (
            <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
          ) : mcqBookmarks?.length ? (
            <div className="space-y-3">
              {mcqBookmarks.map((item) => (
                <div
                  key={item.id}
                  className="rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
                >
                  <p>{item.question_text.slice(0, 160)}</p>
                  <Badge className="mt-2">{item.difficulty}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--color-text-muted)]">No MCQ bookmarks yet.</p>
          )}
        </Card>
      )}

      {tab === 'coding' && (
        <>
          <CodingProblemList
            problems={codingBookmarks?.items ?? []}
            total={codingBookmarks?.total ?? 0}
            isLoading={codingLoading}
          />
          <p className="text-xs text-[var(--color-text-muted)]">
            Open a problem from{' '}
            <Link to="/practice/dsa" className="text-[var(--color-accent)] hover:underline">
              DSA Practice
            </Link>{' '}
            to continue coding.
          </p>
        </>
      )}

      {tab === 'sql' && (
        <>
          <SqlProblemList
            problems={sqlBookmarks?.items ?? []}
            total={sqlBookmarks?.total ?? 0}
            isLoading={sqlLoading}
          />
          <p className="text-xs text-[var(--color-text-muted)]">
            Open a problem from{' '}
            <Link to="/practice/sql" className="text-[var(--color-accent)] hover:underline">
              SQL Practice
            </Link>{' '}
            to continue querying.
          </p>
        </>
      )}

      {tab === 'prompt' && (
        <Card>
          <CardHeader title={`Prompt challenge bookmarks (${promptBookmarks?.length ?? 0})`} />
          {promptLoading ? (
            <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
          ) : promptBookmarks?.length ? (
            <div className="space-y-3">
              {promptBookmarks.map((item) => (
                <Link
                  key={item.id}
                  to={`/ai/prompt-engineering/challenges/${item.slug}`}
                  className="block rounded-md border border-[var(--color-border)] px-3 py-2 text-sm"
                >
                  <p>{item.title}</p>
                  <Badge className="mt-2">{item.difficulty}</Badge>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--color-text-muted)]">No prompt challenge bookmarks yet.</p>
          )}
        </Card>
      )}
    </div>
  )
}
