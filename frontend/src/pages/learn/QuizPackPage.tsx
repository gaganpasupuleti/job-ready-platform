import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

import { Button } from '@/components/common/Button'
import { LearnSubnav } from '@/components/learn/LearnSubnav'
import { fetchStudioCatalog, startPack } from '@/services/studioService'

export function QuizPackPage() {
  const { key = '' } = useParams()
  const navigate = useNavigate()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['studio-catalog', 'quiz', key],
    queryFn: () => fetchStudioCatalog({}),
  })
  const pack = data?.packs.find((item) => item.key === key)
  const start = useMutation({
    mutationFn: () => startPack(key),
    onSuccess: (result) => navigate(`/practice/sessions/${result.session_id}`),
  })

  return (
    <div className="module-page learn-page">
      <LearnSubnav />
      {isLoading ? (
        <p>Loading quiz...</p>
      ) : isError ? (
        <p role="alert">Unable to load quizzes.</p>
      ) : !pack ? (
        <p>No published quiz matches this link.</p>
      ) : (
        <>
          <header className="module-heading">
            <div>
              <p className="eyebrow">{pack.kind === 'crt' ? 'Campus Recruitment Training' : 'Technical quiz'}</p>
              <h1>{pack.title}</h1>
              <p>{pack.questions} questions. Answers stay hidden until the existing practice rules reveal them. Running a query or marking a material read does not complete this quiz.</p>
            </div>
          </header>
          <Button onClick={() => start.mutate()} disabled={start.isPending}>Start quiz</Button>
          {start.isError && <p role="alert">Unable to start this quiz.</p>}
        </>
      )}
    </div>
  )
}
