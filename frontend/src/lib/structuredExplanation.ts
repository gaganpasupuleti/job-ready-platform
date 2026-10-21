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

/** Material or syllabus keys that already have a published lesson page. */
const PUBLISHED_LESSON_HREFS: Record<string, string> = {
  'crt-quant-percentages': '/learn/syllabus/syl-crt-quant-percentages',
  'crt-logical-patterns': '/learn/syllabus/syl-crt-logical-patterns',
  'crt-verbal-meaning': '/learn/syllabus/syl-crt-verbal-meaning',
  'crt-di-tables': '/learn/syllabus/syl-crt-di-tables',
  'dsa-complexity': '/learn/syllabus/syl-dsa-complexity',
  'dsa-arrays-strings': '/learn/syllabus/syl-dsa-arrays-strings',
  'crt-sprint-profit-loss': '/learn/syllabus/syl-sprint-profit',
  'crt-sprint-time-work': '/learn/syllabus/syl-sprint-time-work',
  'crt-sprint-probability': '/learn/syllabus/syl-sprint-probability',
  'crt-sprint-syllogisms': '/learn/syllabus/syl-crt-logical-syllogisms',
  'crt-sprint-grammar': '/learn/syllabus/syl-crt-verbal-grammar',
  'crt-sprint-vocabulary': '/learn/syllabus/syl-sprint-vocabulary',
  'crt-sprint-charts': '/learn/syllabus/syl-crt-di-charts',
  'dsa-sprint-complexity': '/learn/syllabus/syl-sprint-complexity',
  'dsa-sprint-strings': '/learn/syllabus/syl-sprint-strings',
  'dsa-sprint-searching': '/learn/syllabus/syl-sprint-searching',
}

const CORRECT_ANSWER = /^Correct answer:\s*(.*)$/
const RELATED_LESSON = /^([a-z0-9-]+) — ([^.\n]+)\.\s*([\s\S]*)$/

export interface RelatedLessonLink {
  href: string
  title: string
  note: string
}

export function relatedLessonLink(body: string): RelatedLessonLink | null {
  const match = RELATED_LESSON.exec(body.trim())
  if (!match) return null
  const href = PUBLISHED_LESSON_HREFS[match[1]]
  if (!href || !href.startsWith('/learn/syllabus/')) return null
  return { href, title: match[2].trim(), note: match[3].trim() }
}

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
    const correct = CORRECT_ANSWER.exec(trimmed)
    if (correct) {
      flush()
      heading = 'Correct answer'
      lines = [correct[1]]
      continue
    }
    lines.push(line)
  }
  flush()
  return sections.length > 0 ? sections : [{ heading: null, body: text }]
}
