import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { SafeMarkdown } from '@/components/learn/SafeMarkdown'
import { LearnSubnav } from '@/components/learn/LearnSubnav'
import { apiClient } from '@/api/client'
import { fetchMaterial, markMaterialRead, materialDownloadUrl } from '@/services/studioService'

export function MaterialDetailPage() {
  const { key = '' } = useParams()
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['studio-material', key],
    queryFn: () => fetchMaterial(key),
    enabled: Boolean(key),
  })
  const readMutation = useMutation({
    mutationFn: () => markMaterialRead(key),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['studio-material', key] }),
  })

  async function download() {
    const response = await apiClient.get(materialDownloadUrl(key), { responseType: 'blob' })
    const url = URL.createObjectURL(response.data)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${key}.md`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="module-page learn-page">
      <LearnSubnav />
      {isLoading ? (
        <p>Loading material...</p>
      ) : isError || !data ? (
        <p role="alert">Unable to load this material.</p>
      ) : (
        <>
          <header className="module-heading">
            <div>
              <p className="eyebrow">{data.kind} · {data.level} · {data.minutes} min</p>
              <h1>{data.title}</h1>
              <p>{data.summary}</p>
            </div>
          </header>
          <p className="text-sm text-[var(--color-text-muted)]">
            Version {data.version}
            {data.updated_at ? ` · Updated ${data.updated_at.slice(0, 10)}` : ''}
            {data.audience ? ` · Audience ${data.audience}` : ''}
          </p>
          <section className="mt-4">
            <h2 className="text-sm font-semibold">Objectives</h2>
            <ul className="list-disc pl-5 text-sm">{data.objectives.map((item) => <li key={item}>{item}</li>)}</ul>
          </section>
          <div className="mt-4 min-w-0 rounded-[5px] border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
            <SafeMarkdown source={data.body_md} />
          </div>
          {data.examples.length > 0 && (
            <section className="mt-4">
              <h2 className="text-sm font-semibold">Examples</h2>
              {data.examples.map((item) => (
                <pre key={item} className="mt-2 overflow-x-auto rounded bg-[var(--color-surface-muted)] p-3 text-xs">{item}</pre>
              ))}
            </section>
          )}
          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => readMutation.mutate()} disabled={data.read}>
              {data.read ? 'Marked read' : 'Mark as read'}
            </Button>
            {data.has_download && (
              <Button variant="ghost" onClick={() => void download()}>Download Markdown</Button>
            )}
            {data.related_pack && (
              <Link to={`/learn/quizzes/${data.related_pack}`} className="text-sm text-[var(--color-accent)]">
                Start related quiz
              </Link>
            )}
          </div>
          <p className="mt-3 text-xs text-[var(--color-text-muted)]">Marked read is self-reported. It is not assessed competence.</p>
        </>
      )}
    </div>
  )
}
