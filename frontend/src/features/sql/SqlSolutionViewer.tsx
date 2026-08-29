import { Card } from '@/components/common/Card'
import { SqlEditor } from '@/features/sql/SqlEditor'
import type { SqlSolutionResponse } from '@/types/sql'

interface SqlSolutionViewerProps {
  solution: SqlSolutionResponse
}

export function SqlSolutionViewer({ solution }: SqlSolutionViewerProps) {
  return (
    <div className="space-y-4">
      <Card padding="md">
        <h4 className="mb-2 text-sm font-medium">Solution query</h4>
        <div className="h-48 overflow-hidden rounded-md border border-[var(--color-border)]">
          <SqlEditor value={solution.solution_query} onChange={() => {}} readOnly height="100%" />
        </div>
      </Card>

      {solution.solution_explanation && (
        <Card padding="md">
          <h4 className="mb-2 text-sm font-medium">Explanation</h4>
          <p className="whitespace-pre-wrap text-sm text-[var(--color-text-muted)]">
            {solution.solution_explanation}
          </p>
        </Card>
      )}

      {solution.alternate_solution && (
        <Card padding="md">
          <h4 className="mb-2 text-sm font-medium">Alternate solution</h4>
          <div className="h-40 overflow-hidden rounded-md border border-[var(--color-border)]">
            <SqlEditor
              value={solution.alternate_solution}
              onChange={() => {}}
              readOnly
              height="100%"
            />
          </div>
        </Card>
      )}

      {solution.key_concepts.length > 0 && (
        <Card padding="md">
          <h4 className="mb-2 text-sm font-medium">Key concepts</h4>
          <ul className="list-inside list-disc text-sm text-[var(--color-text-muted)]">
            {solution.key_concepts.map((concept) => (
              <li key={concept}>{concept}</li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
