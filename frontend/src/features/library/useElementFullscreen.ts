import { useCallback, useEffect, useRef, useState } from 'react'

export function useElementFullscreen<T extends HTMLElement>() {
  const ref = useRef<T | null>(null)
  const [active, setActive] = useState(false)

  useEffect(() => {
    const onChange = () => setActive(document.fullscreenElement === ref.current)
    document.addEventListener('fullscreenchange', onChange)
    return () => document.removeEventListener('fullscreenchange', onChange)
  }, [])

  const toggle = useCallback(() => {
    const el = ref.current
    if (!el) return
    if (document.fullscreenElement === el) {
      void document.exitFullscreen()
      return
    }
    void el.requestFullscreen()
  }, [])

  return { ref, active, toggle }
}
