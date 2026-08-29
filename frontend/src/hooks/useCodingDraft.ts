import { useCallback, useEffect, useRef, useState } from 'react'

function draftKey(userId: string, problemId: string, languageId: number) {
  return `coding-draft:${userId}:${problemId}:${languageId}`
}

export function useCodingDraft(
  userId: string | undefined,
  problemId: string,
  languageId: number,
  starterCode: string,
) {
  const [sourceCode, setSourceCode] = useState(starterCode)
  const [initialized, setInitialized] = useState(false)
  const skipSaveRef = useRef(false)

  useEffect(() => {
    if (!userId || !problemId) return
    skipSaveRef.current = true
    const stored = localStorage.getItem(draftKey(userId, problemId, languageId))
    setSourceCode(stored ?? starterCode)
    setInitialized(true)
    skipSaveRef.current = false
  }, [userId, problemId, languageId, starterCode])

  useEffect(() => {
    if (!userId || !problemId || !initialized || skipSaveRef.current) return
    localStorage.setItem(draftKey(userId, problemId, languageId), sourceCode)
  }, [userId, problemId, languageId, sourceCode, initialized])

  const resetCode = useCallback(() => {
    if (userId && problemId) {
      localStorage.removeItem(draftKey(userId, problemId, languageId))
    }
    skipSaveRef.current = true
    setSourceCode(starterCode)
    skipSaveRef.current = false
  }, [userId, problemId, languageId, starterCode])

  return { sourceCode, setSourceCode, resetCode, initialized }
}
