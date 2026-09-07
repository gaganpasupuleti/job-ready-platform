import type { SqlProblemDetail } from '@/types/sql'

export type SqlSkillTag =
  | 'SELECT'
  | 'WHERE'
  | 'GROUP BY'
  | 'HAVING'
  | 'ORDER BY'
  | 'JOIN'
  | 'LEFT JOIN'
  | 'LIMIT'
  | 'DISTINCT'
  | 'COUNT'
  | 'SUM'
  | 'AVG'
  | 'CASE'

export interface SqlConceptGuide {
  title: string
  body: string
}

export interface SqlQuestionLearningContext {
  concept: string
  tables: string[]
  sqlSkills: SqlSkillTag[]
  steps: string[]
  commonMistake: string
  conceptGuides: SqlConceptGuide[]
}

function extractTablesFromSchema(problem: SqlProblemDetail): string[] {
  return problem.schema_tables.map((t) => t.table_name)
}

function detectSqlSkills(problem: SqlProblemDetail): SqlSkillTag[] {
  const haystack = [
    problem.description,
    problem.task_description,
    problem.scenario ?? '',
    ...(problem.hints ?? []),
    ...(problem.tags ?? []),
    problem.topic_name ?? '',
  ]
    .join('\n')
    .toUpperCase()

  const skills: SqlSkillTag[] = ['SELECT']

  if (/\bLEFT\s*JOIN\b/.test(haystack) || haystack.includes('LEFT JOIN')) skills.push('LEFT JOIN')
  else if (/\bJOIN\b/.test(haystack)) skills.push('JOIN')

  if (/\bWHERE\b/.test(haystack) || haystack.includes('FILTER')) skills.push('WHERE')
  if (/\bGROUP\s*BY\b/.test(haystack) || haystack.includes('AGGREGAT')) skills.push('GROUP BY')
  if (/\bHAVING\b/.test(haystack)) skills.push('HAVING')
  if (/\bORDER\s*BY\b/.test(haystack) || haystack.includes('SORT')) skills.push('ORDER BY')
  if (/\bLIMIT\b/.test(haystack) || haystack.includes('TOP ')) skills.push('LIMIT')
  if (/\bDISTINCT\b/.test(haystack)) skills.push('DISTINCT')
  if (/\bCOUNT\b/.test(haystack)) skills.push('COUNT')
  if (/\bSUM\b/.test(haystack)) skills.push('SUM')
  if (/\bAVG\b/.test(haystack) || haystack.includes('AVERAGE')) skills.push('AVG')
  if (/\bCASE\b/.test(haystack)) skills.push('CASE')

  return skills
}

function buildSteps(problem: SqlProblemDetail, skills: SqlSkillTag[]): string[] {
  const steps: string[] = [
    `Read the task and note the expected columns: ${problem.expected_columns.join(', ') || 'see problem'}.`,
  ]

  const tables = extractTablesFromSchema(problem)
  if (tables.length === 1) {
    steps.push(`Start from the ${tables[0]} table.`)
  } else if (tables.length > 1) {
    steps.push(`Use these tables: ${tables.join(', ')}.`)
  }

  if (skills.includes('JOIN') || skills.includes('LEFT JOIN')) {
    steps.push('Connect tables with JOIN (or LEFT JOIN) on matching key columns.')
  }
  if (skills.includes('WHERE')) {
    steps.push('Add WHERE to filter individual rows before any grouping.')
  }
  if (skills.includes('GROUP BY')) {
    steps.push('Add GROUP BY for each non-aggregated column you SELECT.')
  }
  if (skills.includes('COUNT') || skills.includes('SUM') || skills.includes('AVG')) {
    steps.push('Use an aggregate function (COUNT, SUM, or AVG) to summarize values.')
  }
  if (skills.includes('HAVING')) {
    steps.push('Add HAVING to filter grouped results (not the same as WHERE).')
  }
  if (skills.includes('ORDER BY')) {
    steps.push('Add ORDER BY to sort the final result.')
  }
  if (skills.includes('LIMIT')) {
    steps.push('Use LIMIT when the task asks for top N or first N rows.')
  }

  steps.push('Run the query, then Submit when the columns and values look right.')
  return steps.slice(0, 6)
}

function buildCommonMistake(skills: SqlSkillTag[]): string {
  if (skills.includes('HAVING') && skills.includes('WHERE')) {
    return 'Using WHERE on an aggregate — put row filters in WHERE and group filters in HAVING.'
  }
  if (skills.includes('HAVING')) {
    return 'Putting HAVING before GROUP BY, or using WHERE instead of HAVING to filter counts.'
  }
  if (skills.includes('GROUP BY')) {
    return 'Selecting a column that is not in GROUP BY and not inside an aggregate function.'
  }
  if (skills.includes('LEFT JOIN')) {
    return 'Using INNER JOIN when the task says to keep all rows from the left table.'
  }
  if (skills.includes('JOIN')) {
    return 'Forgetting the ON condition or joining on the wrong key column.'
  }
  if (skills.includes('ORDER BY')) {
    return 'Sorting by the wrong column, or using DESC when ascending is required.'
  }
  if (skills.includes('WHERE')) {
    return 'Comparing text without quotes, or filtering the wrong column.'
  }
  return 'Selecting extra columns that are not listed in Expected columns.'
}

function buildConceptGuides(skills: SqlSkillTag[]): SqlConceptGuide[] {
  const guides: SqlConceptGuide[] = []
  if (skills.includes('GROUP BY')) {
    guides.push({
      title: 'GROUP BY',
      body:
        'GROUP BY creates one summary row per group. Every normal column in SELECT must appear in GROUP BY. Functions like COUNT(*), SUM(), and AVG() calculate totals across each group.',
    })
  }
  if (skills.includes('HAVING')) {
    guides.push({
      title: 'HAVING vs WHERE',
      body:
        'WHERE filters rows before grouping. HAVING filters groups after GROUP BY — use it for conditions on COUNT(*), SUM(), AVG(), or other aggregates.',
    })
  }
  if (skills.includes('ORDER BY')) {
    guides.push({
      title: 'ORDER BY',
      body:
        'ORDER BY sorts the final result. ASC (default) goes A→Z or low→high. DESC goes high→low.',
    })
  }
  if (skills.includes('JOIN')) {
    guides.push({
      title: 'JOIN',
      body:
        'JOIN combines rows from two tables when keys match in the ON clause. Only matching rows from both sides appear in an INNER JOIN.',
    })
  }
  if (skills.includes('LEFT JOIN')) {
    guides.push({
      title: 'LEFT JOIN',
      body:
        'LEFT JOIN keeps every row from the left table. When no match exists on the right, right-side columns are NULL.',
    })
  }
  return guides
}

export function buildQuestionLearningContext(
  problem: SqlProblemDetail,
): SqlQuestionLearningContext {
  const sqlSkills = detectSqlSkills(problem)
  return {
    concept: problem.topic_name || 'SQL practice',
    tables: extractTablesFromSchema(problem),
    sqlSkills,
    steps: buildSteps(problem, sqlSkills),
    commonMistake: buildCommonMistake(sqlSkills),
    conceptGuides: buildConceptGuides(sqlSkills),
  }
}
