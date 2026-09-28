import { cn } from '@/utils/cn'

/** JobReady JR monogram from design-reference/jobready-v4. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      className={cn('jr-logo', className)}
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M5 7h12v19c0 6-3 9-8 9H5v-7h4c1 0 1-1 1-2V14H5V7Z"
        fill="currentColor"
      />
      <path
        d="M21 7h8c7 0 11 4 11 10 0 4-2 7-5 9l5 9h-9l-6-13h4c3 0 4-2 4-5s-2-4-5-4v22h-7V7Z"
        fill="currentColor"
      />
    </svg>
  )
}

export function Logo({
  className,
  showWordmark = true,
}: {
  className?: string
  showWordmark?: boolean
}) {
  return (
    <>
      <LogoMark className={className} />
      {showWordmark ? (
        <span>
          jobready<span className="brand-period">.</span>
        </span>
      ) : null}
    </>
  )
}
