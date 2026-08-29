/** Judge0 language IDs aligned with backend SUPPORTED_LANGUAGES. */
export const LANGUAGE_MAP = {
  71: { id: 71, name: 'Python 3', monacoId: 'python', shortLabel: 'Python' },
  62: { id: 62, name: 'Java', monacoId: 'java', shortLabel: 'Java' },
  54: { id: 54, name: 'C++ (GCC)', monacoId: 'cpp', shortLabel: 'C++' },
  63: { id: 63, name: 'JavaScript (Node.js)', monacoId: 'javascript', shortLabel: 'JS' },
} as const

export type SupportedLanguageId = keyof typeof LANGUAGE_MAP

export const SUPPORTED_LANGUAGE_IDS = Object.keys(LANGUAGE_MAP).map(Number) as SupportedLanguageId[]

export const SUPPORTED_LANGUAGES = SUPPORTED_LANGUAGE_IDS.map((id) => LANGUAGE_MAP[id])

export function getMonacoLanguage(languageId: number): string {
  return LANGUAGE_MAP[languageId as SupportedLanguageId]?.monacoId ?? 'python'
}

export function getLanguageName(languageId: number): string {
  return LANGUAGE_MAP[languageId as SupportedLanguageId]?.name ?? `Language ${languageId}`
}
