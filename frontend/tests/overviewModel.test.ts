import assert from 'node:assert/strict'
import test from 'node:test'

import {
  mcqAccuracyState,
  practiceCatalogHref,
  quizStatusCounts,
  recentPracticeHref,
  sectionStaleMessage,
  sectionUnavailable,
  visibleQuizzes,
} from '../src/features/dashboard/overviewModel.ts'

const id = '913546e1-9047-445c-a829-d5c3b9b3ea3d'

test('recent practice links use the saved record, not a catalog open', () => {
  assert.equal(recentPracticeHref({ kind: 'mcq_session', source_id: id, status: 'active' }), `/practice/sessions/${id}`)
  assert.equal(
    recentPracticeHref({ kind: 'mcq_session', source_id: id, status: 'completed' }),
    `/practice/sessions/${id}/results`,
  )
  assert.equal(recentPracticeHref({ kind: 'coding_submit', source_id: id, status: 'accepted' }), `/submissions/${id}`)
  assert.equal(recentPracticeHref({ kind: 'sql_submit', source_id: id, status: 'accepted' }), `/sql/submissions/${id}`)
  assert.equal(recentPracticeHref({ kind: 'mcq_session', source_id: 'not-an-id', status: 'active' }), null)
})

test('quiz links stay on existing catalogs and are not called new', () => {
  assert.equal(practiceCatalogHref('Aptitude'), '/practice/aptitude')
  assert.equal(practiceCatalogHref('Operating Systems'), '/practice/mcq')
  const counts = quizStatusCounts([
    { topic_slug: 'a', topic_name: 'A', category_name: 'Aptitude', attempt_status: 'not_started' },
    { topic_slug: 'b', topic_name: 'B', category_name: 'Technical', attempt_status: 'in_progress' },
    { topic_slug: 'c', topic_name: 'C', category_name: 'Technical', attempt_status: 'completed' },
  ])
  assert.deepEqual(counts, { not_started: 1, in_progress: 1, completed: 1 })
  assert.equal(
    visibleQuizzes([
      { topic_slug: 'c', topic_name: 'C', category_name: 'Technical', attempt_status: 'completed' },
      { topic_slug: 'a', topic_name: 'A', category_name: 'Aptitude', attempt_status: 'not_started' },
      { topic_slug: 'b', topic_name: 'B', category_name: 'Technical', attempt_status: 'in_progress' },
    ])[0].attempt_status,
    'in_progress',
  )
})

test('null MCQ accuracy stays empty and a failed refresh keeps loaded data', () => {
  assert.deepEqual(mcqAccuracyState(null), { kind: 'empty' })
  assert.deepEqual(mcqAccuracyState(40), { kind: 'value', label: '40%' })
  const loaded = { data: { week: true }, isError: true, fetchStatus: 'idle' }
  assert.equal(sectionUnavailable(loaded), false)
  assert.match(sectionStaleMessage(loaded, true) ?? '', /last loaded data/)
  assert.equal(sectionUnavailable({ data: undefined, isError: false, fetchStatus: 'paused' }), true)
  assert.equal(sectionStaleMessage({ data: undefined, isError: true, fetchStatus: 'idle' }, false), null)
})
