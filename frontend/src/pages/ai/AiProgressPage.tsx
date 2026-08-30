import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Card, CardHeader } from '@/components/common/Card'
import { fetchAiProgress } from '@/services/aiService'

export function AiProgressPage() {
  const { data, isLoading } = useQuery({ queryKey: ['ai-progress'], queryFn: fetchAiProgress })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">AI Progress</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          MCQ accuracy and prompt mastery by track. This is practice telemetry, not a job-readiness score.
        </p>
      </div>
      {isLoading && <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>}
      {data && (
        <>
          <Card>
            <CardHeader title="By track" />
            <div className="space-y-3">
              {data.topics.map((topic) => (
                <div key={topic.key} className="rounded border border-[var(--color-border)] p-3 text-sm">
                  <p className="font-medium">{topic.label}</p>
                  <p className="text-[var(--color-text-muted)]">
                    MCQ {topic.mcq_attempts} attempts
                    {topic.mcq_accuracy != null ? ` · ${topic.mcq_accuracy}%` : ' · no attempts'}
                  </p>
                  {topic.key === 'prompt' && (
                    <p className="text-[var(--color-text-muted)]">
                      Prompt attempts {topic.prompt_attempts} · mastered {topic.prompt_mastered} · best{' '}
                      {topic.best_prompt_score}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <CardHeader title="Weak topics" />
            {data.weak_topics?.length ? (
              <ul className="list-disc pl-5 text-sm">
                {data.weak_topics.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[var(--color-text-muted)]">No weak topics yet.</p>
            )}
            <Link to="/ai" className="mt-3 inline-block text-sm text-[var(--color-accent)] hover:underline">
              Back to AI home
            </Link>
          </Card>
        </>
      )}
    </div>
  )
}
