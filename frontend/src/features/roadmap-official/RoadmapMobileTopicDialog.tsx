import { useEffect, useRef } from 'react'

interface RoadmapMobileTopicDialogProps {
  open: boolean
  onClose: () => void
  label: string
  children: React.ReactNode
}

export function RoadmapMobileTopicDialog({
  open,
  onClose,
  label,
  children,
}: RoadmapMobileTopicDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const returnFocusRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open) {
      returnFocusRef.current = document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null
      if (!dialog.open) dialog.showModal()
      const closeBtn = dialog.querySelector<HTMLElement>('[data-topic-dialog-close]')
      closeBtn?.focus()
      return
    }
    if (dialog.open) dialog.close()
    returnFocusRef.current?.focus()
    returnFocusRef.current = null
  }, [open])

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    const onCancel = (event: Event) => {
      event.preventDefault()
      onClose()
    }
    dialog.addEventListener('cancel', onCancel)
    return () => dialog.removeEventListener('cancel', onCancel)
  }, [onClose])

  return (
    <dialog ref={dialogRef} className="ors-mobile-dialog" aria-label={label} onClose={onClose}>
      <div className="ors-mobile-dialog-panel">{children}</div>
    </dialog>
  )
}
