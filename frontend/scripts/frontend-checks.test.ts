import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { describe, it } from 'node:test'
import { marked, type Token, type Tokens } from 'marked'

import { approvedLearningImageSrc, learningSvgIsStatic, splitLessonParagraph } from '../src/lib/learningVisuals.ts'

import { capabilityNotice, mergeLanguageChoices, resolveLanguageId, runControlState } from '../src/lib/codingRuntime.ts'
import { isDroppedMarkdownToken, omitChromeOwnedBlocks, prepareRichText, safeHref } from '../src/lib/richText.ts'
import { canOfferRegistration } from '../src/lib/authPolicy.ts'
import { addedToJobReadyLabel, employerPostedLabel, isPortalDate, portalAddedParams } from '../src/lib/jobPortalDates.ts'
import { googleDestination, resolveGoogleClientId } from '../src/lib/googleAuth.ts'
import {
  continuationAction,
  materialKindLabel,
  sharedDestinationNote,
  coverageLabel,
  knownCount,
  knownPercent,
  reviewTopicLabel,
  showGlobalWeakTopics,
  jobsRecommendationCopy,
  lessonPanelTabs,
  mistakeAction,
  nextLessonAction,
  practiceCountLabel,
  readinessScoreLabel,
  sqlWeakTopic,
} from '../src/lib/studentLabels.ts'

function collectLinks(tokens: Token[], kept: string[], dropped: string[]) {
  for (const token of tokens) {
    if (isDroppedMarkdownToken(token.type)) continue
    if (token.type === 'link') {
      const link = token as Tokens.Link
      const href = safeHref(link.href)
      if (href) kept.push(href)
      else dropped.push(link.href)
    }
    const nested = token as Token & { tokens?: Token[]; items?: Array<{ tokens?: Token[] }> }
    if (nested.tokens) collectLinks(nested.tokens, kept, dropped)
    for (const item of nested.items ?? []) {
      if (item.tokens) collectLinks(item.tokens, kept, dropped)
    }
  }
}

describe('markdown safety', () => {
  it('drops unsafe links and raw html tokens', () => {
    assert.equal(safeHref('javascript:alert(1)'), null)
    assert.equal(safeHref('data:text/html,hi'), null)
    assert.equal(safeHref('//evil.example'), null)
    assert.equal(safeHref('https://example.com/docs'), 'https://example.com/docs')
    assert.equal(safeHref('/jobs/preferences'), '/jobs/preferences')
    assert.equal(isDroppedMarkdownToken('html'), true)

    const tokens = marked.lexer(
      'See [ok](https://example.com) and [bad](javascript:alert(1)).\n\n<script>alert(1)</script>',
      { gfm: true },
    )
    const kept: string[] = []
    const dropped: string[] = []
    collectLinks(tokens, kept, dropped)
    assert.deepEqual(kept, ['https://example.com'])
    assert.equal(dropped.some((href) => href.startsWith('javascript:')), true)
    assert.equal(tokens.some((token) => token.type === 'html'), true)
  })

  it('turns escaped list markers into list items', () => {
    const tokens = marked.lexer(prepareRichText('\\* Build APIs\n\\* Write tests'), { gfm: true, breaks: false })
    const list = tokens.find((token) => token.type === 'list') as Tokens.List | undefined
    assert.equal(list?.items.length, 2)
  })

  it('omits a duplicate title and a chrome-owned objectives block without stripping later prose', () => {
    const tokens = marked.lexer(
      '# Prompt Engineering\n\n## Learning objectives\n\n- Write a prompt\n\nThe learning objectives stay useful in this paragraph.\n\n## Example\n\nKeep this section.',
      { gfm: true },
    )
    const kept = omitChromeOwnedBlocks(tokens, {
      title: 'Prompt Engineering',
      headings: ['Learning objectives'],
    })
    const headings = kept.filter((token) => token.type === 'heading').map((token) => token.text)
    assert.deepEqual(headings, ['Example'])
    const paragraph = kept.find((token) => token.type === 'paragraph')
    assert.match(paragraph?.text ?? '', /learning objectives stay useful/)
  })
})

describe('sql recommendation and results links', () => {
  it('ignores a non-sql weak topic', () => {
    const topic = sqlWeakTopic([
      { source_type: 'mcq', status: 'open', title: 'Probability', occurrence_count: 4 },
      { source_type: 'sql', status: 'open', title: 'Joins', occurrence_count: 2 },
    ])
    assert.equal(topic && !topic.empty && topic.title, 'Joins')
    assert.deepEqual(sqlWeakTopic([{ source_type: 'mcq', status: 'open', title: 'Probability' }]), { empty: true })
    assert.equal(sqlWeakTopic(null), null)
  })

  it('labels a results link as view results', () => {
    const action = mistakeAction('/practice/sessions/abc/results')
    assert.equal(action?.label, 'View results')
    assert.match(action?.note ?? '', /cannot be retried/)
    assert.equal(mistakeAction('/practice/sql/joins')?.label, 'Retry')
  })
})

describe('language selection', () => {
  const languages = [
    { id: 71, name: 'Python', available: false },
    { id: 62, name: 'Java', available: true },
  ]

  it('keeps listed languages and selects a runnable one', () => {
    const merged = mergeLanguageChoices(languages, [], [{ id: 62, name: 'Java (OpenJDK)', available: true }])
    assert.deepEqual(
      merged.map((lang) => lang.id),
      [71, 62],
    )
    assert.equal(merged[1]?.name, 'Java (OpenJDK)')
    assert.equal(resolveLanguageId(null, merged), 62)
    assert.equal(resolveLanguageId(71, merged), 71)
  })

  it('enables run only when the runtime and language are available', () => {
    assert.equal(
      runControlState({
        statusPending: true,
        statusError: false,
        executionAvailable: undefined,
        problemExecutionAvailable: true,
        languageAvailable: true,
      }).reason,
      'checking',
    )
    assert.equal(
      runControlState({
        statusPending: false,
        statusError: false,
        executionAvailable: true,
        problemExecutionAvailable: true,
        languageAvailable: true,
      }).enabled,
      true,
    )
    assert.equal(
      runControlState({
        statusPending: false,
        statusError: false,
        executionAvailable: false,
        problemExecutionAvailable: true,
        languageAvailable: true,
      }).reason,
      'runtime',
    )
    assert.equal(
      runControlState({
        statusPending: false,
        statusError: false,
        executionAvailable: true,
        problemExecutionAvailable: true,
        languageAvailable: false,
      }).reason,
      'language',
    )
  })
})

describe('jobs, readiness, practice counts, and continuation', () => {
  it('separates configured and unconfigured job lists', () => {
    const unconfigured = jobsRecommendationCopy({
      preferencesError: false,
      configured: false,
      scored: false,
      hasItems: true,
    })
    assert.match(unconfigured.summary, /not a personalized match/)
    assert.equal(unconfigured.showPreferencesLink, true)
    const fallback = jobsRecommendationCopy({
      preferencesError: false,
      configured: true,
      targetName: 'Data Engineer',
      scored: false,
      hasItems: true,
    })
    assert.match(fallback.summary, /recent openings from the catalog/)
    assert.match(fallback.summary, /not personalized recommendations/)
    assert.doesNotMatch(fallback.summary, /Data Engineer/)
    assert.doesNotMatch(fallback.summary, /related to/)
    assert.equal(fallback.showPreferencesLink, false)
    const scored = jobsRecommendationCopy({
      preferencesError: false,
      configured: true,
      targetName: 'Data Engineer',
      scored: true,
      hasItems: true,
    })
    assert.match(scored.summary, /Openings related to Data Engineer/)
    assert.match(scored.summary, /not a hiring probability/)
    assert.equal(scored.showPreferencesLink, false)
  })

  it('does not turn an unconfigured readiness score or an unknown count into zero', () => {
    assert.equal(
      readinessScoreLabel({
        overallScoreReady: false,
        hasMinimumEvidence: false,
        score: 0,
        hasTargetRole: false,
      }),
      'Not measured yet',
    )
    assert.equal(coverageLabel(0, 0), 'Not measured')
    assert.equal(coverageLabel(0, 2), '0 / 2')
    assert.equal(
      practiceCountLabel({
        itemCount: 0,
        externalRoute: '/practice/sql',
        catalogCount: null,
        catalogState: 'loading',
        availability: 'available',
      }),
      'Count unavailable',
    )
    assert.equal(
      practiceCountLabel({
        itemCount: 0,
        externalRoute: '/practice/sql',
        catalogCount: 18,
        catalogState: 'ready',
        availability: 'coming_soon',
      }),
      '18 items',
    )
    assert.equal(
      practiceCountLabel({
        itemCount: 0,
        externalRoute: null,
        catalogCount: null,
        catalogState: 'idle',
        availability: 'coming_soon',
      }),
      'Not available yet',
    )
  })

  it('uses start or explore unless the link is a saved continuation', () => {
    assert.equal(continuationAction({ href: '/learn/courses/python', progress_percent: 40 }).label, 'Explore')
    assert.equal(
      continuationAction({ href: '/learn/courses/python/intro/variables', progress_percent: 40 }).label,
      'Continue',
    )
    assert.equal(
      continuationAction({ href: '/learn/courses/python/intro/variables', progress_percent: 0 }).label,
      'Start',
    )
    assert.equal(continuationAction({ href: '/practice', progress_percent: 10 }).label, 'Explore')
  })
})

describe('runtime capability notices', () => {
  it('keeps loading, failure, and a known outage distinct', () => {
    assert.equal(capabilityNotice({ pending: true, failed: false, available: undefined, kind: 'code' }).state, 'checking')
    assert.match(capabilityNotice({ pending: false, failed: true, available: undefined, kind: 'sql' }).text, /Could not check/)
    assert.equal(
      capabilityNotice({ pending: false, failed: false, available: false, kind: 'code' }).text,
      'Code execution is coming soon. You can write code and save drafts.',
    )
  })

  it('names runnable languages separately from blocked ones', () => {
    const notice = capabilityNotice({
      pending: false,
      failed: false,
      available: true,
      kind: 'code',
      languages: [
        { id: 62, name: 'Java', available: true },
        { id: 71, name: 'Python', available: false },
      ],
    })
    assert.equal(notice.state, 'ready')
    assert.match(notice.text, /Java/)
    assert.match(notice.text, /Not available: Python/)
    assert.doesNotMatch(notice.text, /Run and Submit are available for Python/)
  })
})

describe('lesson navigation', () => {
  it('blocks next when the curriculum item is locked', () => {
    const next = nextLessonAction({
      nextHref: '/learn/courses/python/intro/loops',
      blocks: [{ module_slug: 'intro', slug: 'loops', status: 'locked', title: 'Loops' }],
    })
    assert.equal(next.kind, 'blocked')
    if (next.kind === 'blocked') assert.match(next.reason, /Loops/)
  })

  it('omits solution and hints on a reading lesson without that content', () => {
    assert.deepEqual(lessonPanelTabs('article', { hasHints: false, hasSolution: false }), ['statement', 'help'])
    assert.ok(lessonPanelTabs('worked_example', { hasHints: false, hasSolution: false }).includes('solution'))
  })
})

describe('phase 5 labels', () => {
  it('names a cheat sheet without repeating an unread status', () => {
    assert.equal(materialKindLabel('cheat_sheet'), 'Cheat sheet')
  })

  it('does not call a track home Continue', () => {
    assert.equal(continuationAction({ href: '/ai', progress_percent: 1 }).label, 'Explore')
    assert.equal(
      continuationAction({ href: '/ai/prompt-engineering/challenges/summarize', progress_percent: 40 }).label,
      'Continue',
    )
  })

  it('says when several tracks open one catalog', () => {
    assert.match(
      sharedDestinationNote('/practice/mcq?topic=rag', ['/practice/mcq', '/practice/mcq?topic=rag']) ?? '',
      /same catalog/,
    )
    assert.equal(sharedDestinationNote('/cloud/iam', ['/cloud/iam', '/devops']), null)
  })
})

describe('review labels and progress figures', () => {
  it('uses a topic name instead of a long question', () => {
    assert.equal(
      reviewTopicLabel({
        title: 'Which index plan is cheaper when the filter matches two rows out of a million stored orders?',
        context: { topic_name: 'Indexes' },
      }),
      'Indexes',
    )
    assert.equal(reviewTopicLabel({ title: 'Indexes' }), 'Indexes')
  })

  it('hides global weak topics once a subject filter is active', () => {
    assert.equal(showGlobalWeakTopics('all'), true)
    assert.equal(showGlobalWeakTopics('mcq'), false)
  })

  it('offers registration only when the API says it is open', () => {
    assert.equal(canOfferRegistration(true), true)
    assert.equal(canOfferRegistration(false), false)
    assert.equal(canOfferRegistration(undefined), false)
    assert.equal(canOfferRegistration(null), false)
  })

  it('keeps Google sign-in hidden until a client id is configured', () => {
    assert.equal(resolveGoogleClientId(undefined, 'e2e-client', true), 'e2e-client')
    assert.equal(resolveGoogleClientId('  real-client  ', 'e2e-client', true), 'real-client')
    assert.equal(resolveGoogleClientId('', 'e2e-client', false), '')
    assert.equal(resolveGoogleClientId(undefined, null, false), '')
  })

  it('sends a new Google student to preferences and an existing student to from', () => {
    assert.equal(googleDestination(true, '/practice'), '/jobs/preferences')
    assert.equal(googleDestination(false, '/practice'), '/practice')
    assert.equal(googleDestination(false, null), '/jobs')
    assert.equal(googleDestination(false, '//evil.example'), '/jobs')
  })

  it('does not turn a missing progress figure into zero', () => {
    assert.equal(knownCount(undefined), '—')
    assert.equal(knownCount(0), '0')
    assert.equal(knownPercent(null), null)
    assert.equal(knownPercent(20), '20%')
  })
})

describe('portal ingestion dates', () => {
  it('keeps employer posting dates separate and does not invent a date', () => {
    assert.equal(employerPostedLabel(null), 'Employer posting date unavailable')
    assert.equal(employerPostedLabel(''), 'Employer posting date unavailable')
    assert.equal(employerPostedLabel('not-a-date'), 'Employer posting date unavailable')
    assert.match(employerPostedLabel('2026-10-09T07:20:00Z'), /^Employer posted /)
    assert.equal(addedToJobReadyLabel(null), 'Added to JobReady date unavailable')
    assert.equal(addedToJobReadyLabel(undefined), 'Added to JobReady date unavailable')
    assert.match(addedToJobReadyLabel('2026-10-09T07:20:00Z'), /^Added to JobReady /)
  })

  it('sends a preset or a custom range, never both', () => {
    assert.deepEqual(portalAddedParams('today', '2026-10-01', '2026-10-03'), {
      added_within: 'today',
      added_from: undefined,
      added_to: undefined,
    })
    assert.deepEqual(portalAddedParams('custom', '2026-10-01', '2026-10-03'), {
      added_within: undefined,
      added_from: '2026-10-01',
      added_to: '2026-10-03',
    })
    assert.deepEqual(portalAddedParams('custom', 'yesterday', '2026-10-03'), {
      added_within: undefined,
      added_from: undefined,
      added_to: '2026-10-03',
    })
    assert.deepEqual(portalAddedParams('', '2026-10-01', '2026-10-03'), {
      added_within: undefined,
      added_from: undefined,
      added_to: undefined,
    })
    assert.equal(isPortalDate('2026-10-09'), true)
    assert.equal(isPortalDate('2026-10-09T00:00:00Z'), false)
  })
})

describe('learning visuals', () => {
  it('accepts approved svg, png, and webp paths only', () => {
    assert.equal(
      approvedLearningImageSrc('/learning-visuals/dsa/binary-search.svg'),
      '/learning-visuals/dsa/binary-search.svg',
    )
    assert.equal(
      approvedLearningImageSrc('/learning-visuals/crt/format-check.png'),
      '/learning-visuals/crt/format-check.png',
    )
    assert.equal(
      approvedLearningImageSrc('/learning-visuals/mcq/format-check.webp'),
      '/learning-visuals/mcq/format-check.webp',
    )
    assert.equal(approvedLearningImageSrc('/learning-visuals/interviews/intro.svg'), '/learning-visuals/interviews/intro.svg')
    for (const blocked of [
      'javascript:alert(1)',
      'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"></svg>',
      '//cdn.example/diagram.svg',
      'https://cdn.example/diagram.svg',
      '/learning-visuals/../secret.svg',
      '/learning-visuals/crt/%2e%2e/secret.svg',
      '/learning-visuals/crt/percentages-quarter.svg/../../secret.svg',
      '/learning-visuals/other/diagram.svg',
      '/learning-visuals/crt/diagram.gif',
      '/etc/passwd',
      'file:///tmp/diagram.svg',
      'blob:https://jobready.local/1',
    ]) {
      assert.equal(approvedLearningImageSrc(blocked), null, blocked)
    }
  })

  it('reads a caption from an image token without enabling html', () => {
    const tokens = marked.lexer(
      '## Visualize\n\n![Quarter of a price](/learning-visuals/crt/percentages-quarter.svg "25% of 240 is 60")\n\n| Step | Result |\n| --- | --- |\n| Sale | 180 |\n\n```text\n240 - 60 = 180\n```\n\n<script>alert(1)</script>',
      { gfm: true },
    )
    const image = tokens.flatMap((token) => (token.type === 'paragraph' ? token.tokens ?? [] : [])).find((token) => token.type === 'image') as Tokens.Image
    assert.equal(image.text, 'Quarter of a price')
    assert.equal(approvedLearningImageSrc(image.href), '/learning-visuals/crt/percentages-quarter.svg')
    assert.equal(image.title, '25% of 240 is 60')
    assert.equal(tokens.some((token) => token.type === 'table'), true)
    assert.equal(tokens.some((token) => token.type === 'code'), true)
    assert.equal(tokens.some((token) => token.type === 'html'), true)
    assert.equal(tokens.some((token) => token.type === 'heading'), true)
  })

  it('keeps a diagram out of a paragraph that also contains text', () => {
    const tokens = marked.lexer(
      'Before ![Quarter of a price](/learning-visuals/crt/percentages-quarter.svg "25% of 240 is 60") after the picture.\n\n![Blocked script image](javascript:alert(1)) stays text.',
      { gfm: true },
    )
    const mixed = tokens.find((token) => token.type === 'paragraph') as Tokens.Paragraph
    const segments = splitLessonParagraph(mixed.tokens ?? [])
    assert.deepEqual(
      segments.map((segment) => segment.kind),
      ['inline', 'diagram', 'inline'],
    )
    assert.equal(segments[0].kind, 'inline')
    if (segments[0].kind === 'inline') assert.equal(segments[0].tokens.some((token) => token.type === 'text'), true)
    if (segments[2].kind === 'inline') assert.match(segments[2].tokens.map((token) => token.text ?? '').join(''), /after the picture/)
    const blocked = tokens.filter((token) => token.type === 'paragraph')[1] as Tokens.Paragraph
    const blockedSegments = splitLessonParagraph(blocked.tokens ?? [])
    assert.deepEqual(
      blockedSegments.map((segment) => segment.kind),
      ['inline'],
    )
    assert.equal(blockedSegments[0].kind === 'inline' && blockedSegments[0].tokens.some((token) => token.type === 'image'), true)
  })

  it('rejects active content in shipped diagrams', () => {
    const root = path.resolve('public/learning-visuals')
    const files = fs.readdirSync(root, { recursive: true, encoding: 'utf8' }).filter((name) => String(name).endsWith('.svg'))
    assert.equal(files.length, 6)
    for (const file of files) {
      const source = fs.readFileSync(path.join(root, String(file)), 'utf8')
      assert.equal(learningSvgIsStatic(source), true, String(file))
    }
    assert.equal(learningSvgIsStatic('<svg xmlns="http://www.w3.org/2000/svg"></svg>'), true)
    assert.equal(learningSvgIsStatic('<svg><script>alert(1)</script></svg>'), false)
    assert.equal(learningSvgIsStatic('<svg xmlns="http://www.w3.org/2000/svg"><foreignObject></foreignObject></svg>'), false)
    assert.equal(learningSvgIsStatic('<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"></svg>'), false)
    assert.equal(learningSvgIsStatic('<svg xmlns="http://www.w3.org/2000/svg"><a href="/learn">x</a></svg>'), false)
    assert.equal(learningSvgIsStatic('<svg xmlns="http://www.w3.org/2000/svg"><style>rect{fill:url(#x)}</style></svg>'), false)
    assert.equal(learningSvgIsStatic('<svg xmlns="http://www.w3.org/2000/svg"><rect fill="url(#paint)"/></svg>'), false)
    assert.equal(learningSvgIsStatic('<svg xmlns="http://www.w3.org/2000/svg"><animate attributeName="x"/></svg>'), false)
    assert.equal(learningSvgIsStatic('<svg xmlns="http://www.w3.org/2000/svg" href="https://evil.example/a.svg"></svg>'), false)
  })
})
