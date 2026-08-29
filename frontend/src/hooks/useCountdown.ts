import { useEffect, useState } from 'react'

export function useCountdown(expiresAt?: string | null, remainingSeconds?: number | null) {
  const [secondsLeft, setSecondsLeft] = useState<number | null>(() => {
    if (remainingSeconds != null) return remainingSeconds
    if (expiresAt) {
      return Math.max(0, Math.floor((new Date(expiresAt).getTime() - Date.now()) / 1000))
    }
    return null
  })

  useEffect(() => {
    if (remainingSeconds != null) {
      setSecondsLeft(remainingSeconds)
      return
    }
    if (expiresAt) {
      setSecondsLeft(
        Math.max(0, Math.floor((new Date(expiresAt).getTime() - Date.now()) / 1000)),
      )
    }
  }, [expiresAt, remainingSeconds])

  useEffect(() => {
    if (secondsLeft == null || secondsLeft <= 0) return
    const timer = window.setInterval(() => {
      setSecondsLeft((prev) => (prev == null || prev <= 0 ? 0 : prev - 1))
    }, 1000)
    return () => window.clearInterval(timer)
  }, [secondsLeft != null && secondsLeft > 0])

  return secondsLeft
}

export function formatCountdown(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}
