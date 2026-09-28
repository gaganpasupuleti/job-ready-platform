export interface RuntimeLanguage {
  id: number
  name: string
  available?: boolean
}

/** Keep every listed language. Overlay live availability from the execution-status payload when it exists. */
export function mergeLanguageChoices(
  problemLanguages: RuntimeLanguage[] | undefined,
  catalog: RuntimeLanguage[] | undefined,
  executionLanguages: RuntimeLanguage[] | undefined,
): RuntimeLanguage[] {
  const base = problemLanguages?.length ? problemLanguages : (catalog ?? [])
  if (!executionLanguages?.length) return base
  const runtime = new Map(executionLanguages.map((lang) => [lang.id, lang]))
  return base.map((lang) => {
    const live = runtime.get(lang.id)
    if (!live) return lang
    return {
      ...lang,
      name: live.name || lang.name,
      available: lang.available !== false && live.available !== false,
    }
  })
}

/** Prefer the student's choice when it is still listed; otherwise the first runnable language. */
export function resolveLanguageId(choice: number | null, options: RuntimeLanguage[]): number | null {
  if (choice != null && options.some((lang) => lang.id === choice)) return choice
  return options.find((lang) => lang.available !== false)?.id ?? options[0]?.id ?? null
}

export type RunControlReason = 'checking' | 'error' | 'ready' | 'language' | 'runtime'

export function runControlState(input: {
  statusPending: boolean
  statusError: boolean
  executionAvailable: boolean | undefined
  problemExecutionAvailable: boolean | undefined
  languageAvailable: boolean | undefined
}): { enabled: boolean; reason: RunControlReason } {
  if (input.statusPending) return { enabled: false, reason: 'checking' }
  if (input.statusError) return { enabled: false, reason: 'error' }
  const runtimeUp = input.executionAvailable === true && input.problemExecutionAvailable !== false
  const languageUp = input.languageAvailable !== false
  if (runtimeUp && languageUp) return { enabled: true, reason: 'ready' }
  if (runtimeUp && !languageUp) return { enabled: false, reason: 'language' }
  return { enabled: false, reason: 'runtime' }
}
