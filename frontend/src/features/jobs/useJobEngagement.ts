import { useEffect } from 'react'

import { recordJobEngagement } from '@/services/jobService'

const TICK_MS = 15_000

/** Count one open, then add visible time while the job page stays open. */
export function useJobEngagement(jobId: string | undefined) {
  useEffect(() => {
    if (!jobId) return
    let last = Date.now()
    let closed = false

    const elapsed = () => {
      const now = Date.now()
      const seconds = Math.min(60, Math.max(0, Math.round((now - last) / 1000)))
      last = now
      return seconds
    }

    const send = (opened: boolean, seconds: number, keepalive = false) => {
      if (closed && !keepalive) return
      if (!opened && seconds <= 0) return
      void recordJobEngagement(jobId, { opened, seconds }, keepalive).catch(() => undefined)
    }

    send(true, 0)

    const timer = window.setInterval(() => {
      if (document.visibilityState !== 'visible') {
        last = Date.now()
        return
      }
      send(false, elapsed())
    }, TICK_MS)

    const onHide = () => {
      if (document.visibilityState === 'hidden') send(false, elapsed(), true)
    }
    document.addEventListener('visibilitychange', onHide)

    return () => {
      closed = true
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', onHide)
      send(false, elapsed(), true)
    }
  }, [jobId])
}
