import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import { fetchAiHome } from '@/services/aiService'

export function AiHomePage() {
  const { data, isLoading } = useQuery({ queryKey: ['ai-home'], queryFn: fetchAiHome })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">AI Practice</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          GenAI, RAG, agents, MCP, and security MCQs plus deterministic prompt challenges. No external LLM
          API is required.
        </p>
      </div>

      {isLoading && <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>}

      {data && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.tracks.map((track) => (
              <Link
                key={track.key}
                to={track.href}
                className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 hover:border-[var(--color-accent)]"
              >
                <h3 className="font-medium text-[var(--color-text)]">{track.label}</h3>
                <p className="mt-1 text-xs text-[var(--color-text-muted)]">Open track</p>
              </Link>
            ))}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader title="Continue AI practice" />
              {data.continue_ai ? (
                <Link to={data.continue_ai} className="text-sm text-[var(--color-accent)] hover:underline">
                  Resume {data.continue_ai}
                </Link>
              ) : (
                <p className="text-sm text-[var(--color-text-muted)]">Start with Generative AI MCQs.</p>
              )}
              <p className="mt-3 text-xs text-[var(--color-text-subtle)]">
                Prompt challenges attempted {data.prompt_progress.attempted} · mastered{' '}
                {data.prompt_progress.mastered}
              </p>
            </Card>
            <Card>
              <CardHeader title="Weak AI topics" />
              {data.weak_topics.length ? (
                <ul className="list-disc pl-5 text-sm text-[var(--color-text)]">
                  {data.weak_topics.map((topic) => (
                    <li key={topic}>{topic}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-[var(--color-text-muted)]">
                  No weak topics yet — complete a few MCQ sessions to see accuracy.
                </p>
              )}
            </Card>
          </div>

          <Card>
            <CardHeader title="MCQ accuracy by topic" />
            <div className="space-y-2">
              {data.topics.map((topic) => (
                <div key={topic.key} className="flex items-center justify-between text-sm">
                  <span>{topic.label}</span>
                  <span className="text-[var(--color-text-muted)]">
                    {topic.mcq_attempts} attempts
                    {topic.mcq_accuracy != null ? ` · ${topic.mcq_accuracy}%` : ''}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <CardHeader title="Recommended next topics" />
            <div className="flex flex-wrap gap-2">
              {data.paths.map((path) => (
                <Link key={path.slug} to={path.href}>
                  <Badge>{path.title}</Badge>
                </Link>
              ))}
              <Link to="/ai/progress" className="text-sm text-[var(--color-accent)] hover:underline">
                Full AI progress
              </Link>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
