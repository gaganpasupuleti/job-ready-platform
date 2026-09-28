import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { marked, type Token, type Tokens } from 'marked'

import { mergeLanguageChoices, resolveLanguageId, runControlState } from '../src/lib/codingRuntime.ts'
import { isDroppedMarkdownToken, omitChromeOwnedBlocks, prepareRichText, safeHref } from '../src/lib/richText.ts'
import {
  continuationAction,
  coverageLabel,
  jobsRecommendationCopy,
  mistakeAction,
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
    const configured = jobsRecommendationCopy({
      preferencesError: false,
      configured: true,
      targetName: 'Data Engineer',
      scored: false,
      hasItems: true,
    })
    assert.match(configured.summary, /Data Engineer/)
    assert.equal(configured.showPreferencesLink, false)
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
