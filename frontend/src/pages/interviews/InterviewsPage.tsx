import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { fetchInterviewQuestion, fetchInterviewQuestions } from '@/services/contentService'

export function InterviewsPage() {
  const [openSlug, setOpenSlug] = useState<string | null>(null)
  const { data, isLoading } = useQuery({
    queryKey: ['interview-questions'],
    queryFn: fetchInterviewQuestions,
  })
  const { data: detail } = useQuery({
    queryKey: ['interview-question', openSlug],
    queryFn: () => fetchInterviewQuestion(openSlug!),
    enabled: Boolean(openSlug),
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text)]">Interview Prep</h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          Approved Q&A only. New content is staged and reviewed before it appears here.
        </p>
      </div>

      {isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
      ) : (
        <div className="space-y-3">
          {(data?.items ?? []).map((item) => (
            <Card key={item.id} padding="md">
              <button
                type="button"
                className="w-full text-left"
                onClick={() => setOpenSlug(item.slug === openSlug ? null : item.slug)}
              >
                <p className="font-medium text-[var(--color-text)]">{item.question_text}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  <Badge>{item.difficulty}</Badge>
                  <Badge>{item.experience_level}</Badge>
                  {item.skills.map((s) => (
                    <Badge key={s}>{s}</Badge>
                  ))}
                </div>
              </button>
              {openSlug === item.slug && detail && (
                <div className="mt-4 border-t border-[var(--color-border)] pt-3 text-sm">
                  <p className="whitespace-pre-wrap text-[var(--color-text)]">{detail.expected_answer}</p>
                  <ul className="mt-2 list-disc pl-5 text-[var(--color-text-muted)]">
                    {detail.key_points.map((p) => (
                      <li key={p.point_text}>{p.point_text}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          ))}
          {!data?.items.length && (
            <p className="text-sm text-[var(--color-text-muted)]">No approved interview questions yet.</p>
          )}
        </div>
      )}
    </div>
  )
}
