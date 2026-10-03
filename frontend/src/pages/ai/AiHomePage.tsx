import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '@/components/common/Badge'
import { Card, CardHeader } from '@/components/common/Card'
import { continuationAction, sharedDestinationNote } from '@/lib/studentLabels'
import { fetchAiHome } from '@/services/aiService'

const TRACK_BLURB: Record<string, string> = {
  genai: 'How models generate text, embeddings, and evaluation.',
  rag: 'Retrieval, chunking, and grounding. Often the same catalog as Generative AI.',
  'prompt-engineering': 'Instruction design and structured outputs, plus prompt challenges.',
  agents: 'Loops, tools, and guardrails. There is no live agent runtime.',
  mcp: 'Host, client, and server concepts. Practice stays in the shared AI catalog.',
  'tool-calling': 'When a model should call a tool, and what it must confirm.',
  evaluation: 'Golden sets and groundedness checks.',
  security: 'Prompt injection and trust boundaries. No offensive labs.',
  'system-design': 'How an assistant, a retriever, and a tool fit together.',
}

export function AiHomePage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ['ai-home'], queryFn: fetchAiHome })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">AI Practice</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          GenAI, RAG, agents, MCP, and security questions, plus prompt challenges. No hosted model is called.
        </p>
      </div>

      {isLoading && <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>}
      {isError && (
        <p className="text-sm text-[var(--color-danger)]" role="alert">
          Unable to load AI practice.
        </p>
      )}

      {data && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.tracks.map((track) => {
              const shared = sharedDestinationNote(track.href, data.tracks.map((item) => item.href))
              return (
                <Link
                  key={track.key}
                  to={track.href}
                  className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 hover:border-[var(--color-accent)]"
                >
                  <h3 className="font-medium text-[var(--color-text)]">{track.label}</h3>
                  <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                    {TRACK_BLURB[track.key] ?? 'Practice questions for this topic.'}
                  </p>
                  {shared ? <p className="mt-2 text-xs text-[var(--color-text-subtle)]">{shared}</p> : null}
                </Link>
              )
            })}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader title="Where to go next" />
              {data.continue_ai ? (
                <Link to={data.continue_ai} className="text-sm text-[var(--color-accent)] hover:underline">
                  {continuationAction({ href: data.continue_ai, progress_percent: 1 }).label} AI practice
                </Link>
              ) : (
                <p className="text-sm text-[var(--color-text-muted)]">No saved AI lesson yet. Open a track above.</p>
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
