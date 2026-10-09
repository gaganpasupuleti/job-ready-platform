/** Labels and query params for the Jobs portal ingestion date.

 * Preset and custom dates are calendar dates interpreted by the API in India
 * Standard Time. A missing timestamp stays unlabeled instead of being shown
 * as an old listing. Employer `posted_at` stays a separate field.
 */

const ADDED_PRESETS = new Set(['today', '3d', '7d', '30d'])

export function isPortalDate(value: string | undefined): boolean {
  return Boolean(value && /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(`${value}T00:00:00Z`)))
}

export function portalAddedParams(selection: string, from?: string, to?: string) {
  if (selection === 'custom') {
    return {
      added_within: undefined,
      added_from: isPortalDate(from) ? from : undefined,
      added_to: isPortalDate(to) ? to : undefined,
    }
  }
  if (ADDED_PRESETS.has(selection)) {
    return { added_within: selection, added_from: undefined, added_to: undefined }
  }
  return { added_within: undefined, added_from: undefined, added_to: undefined }
}

export function employerPostedLabel(postedAt: string | null | undefined): string {
  if (!postedAt) return 'Employer posting date unavailable'
  const date = new Date(postedAt)
  if (Number.isNaN(date.getTime())) return 'Employer posting date unavailable'
  return `Employer posted ${date.toLocaleDateString()}`
}

export function addedToJobReadyLabel(firstSeenAt: string | null | undefined): string {
  if (!firstSeenAt) return 'Added to JobReady date unavailable'
  const date = new Date(firstSeenAt)
  if (Number.isNaN(date.getTime())) return 'Added to JobReady date unavailable'
  return `Added to JobReady ${date.toLocaleDateString()}`
}
