/** Plain-text sections for a reviewed explanation. This does not parse HTML. */

export const EXPLANATION_HEADINGS = [
  'Step-by-step',
  'Why other options are wrong',
  'Learn the concept',
  'Formula or key principle',
  'Worked example',
  'Worked algorithm',
  'Related lesson',
  'Topic metadata',
] as const

export interface ExplanationSection {
  heading: string | null
  body: string
}

const HEADINGS = new Set<string>(EXPLANATION_HEADINGS)

export function splitExplanation(text: string): ExplanationSection[] {
  const sections: ExplanationSection[] = []
  let heading: string | null = null
  let lines: string[] = []
  const flush = () => {
    const body = lines.join('\n').trim()
    if (heading !== null || body) sections.push({ heading, body })
    lines = []
  }
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim()
    if (HEADINGS.has(trimmed)) {
      flush()
      heading = trimmed
      continue
    }
    lines.push(line)
  }
  flush()
  return sections.length > 0 ? sections : [{ heading: null, body: text }]
}
