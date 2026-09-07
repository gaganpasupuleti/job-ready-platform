import type { SqlKeywordCompletion } from '@/features/sql/editor-intelligence/sqlCompletion.types'

export const SQL_KEYWORDS: SqlKeywordCompletion[] = [
  { label: 'SELECT', detail: 'keyword' },
  { label: 'FROM', detail: 'keyword' },
  { label: 'WHERE', detail: 'keyword' },
  { label: 'JOIN', detail: 'keyword' },
  { label: 'INNER JOIN', detail: 'keyword' },
  { label: 'LEFT JOIN', detail: 'keyword' },
  { label: 'ON', detail: 'keyword' },
  { label: 'GROUP BY', detail: 'keyword' },
  { label: 'HAVING', detail: 'keyword' },
  { label: 'ORDER BY', detail: 'keyword' },
  { label: 'LIMIT', detail: 'keyword' },
  { label: 'DISTINCT', detail: 'keyword' },
  { label: 'AS', detail: 'keyword' },
  { label: 'AND', detail: 'keyword' },
  { label: 'OR', detail: 'keyword' },
  { label: 'NOT', detail: 'keyword' },
  { label: 'IS NULL', detail: 'keyword' },
  { label: 'IS NOT NULL', detail: 'keyword' },
  { label: 'BETWEEN', detail: 'keyword' },
  { label: 'IN', detail: 'keyword' },
  { label: 'LIKE', detail: 'keyword' },
  { label: 'WITH', detail: 'keyword' },
]

export const SQL_AGGREGATE_COMPLETIONS: SqlKeywordCompletion[] = [
  { label: 'COUNT()', insertText: 'COUNT(${1:column})', detail: 'aggregate' },
  { label: 'COUNT(*) AS total_count', insertText: 'COUNT(*) AS total_count', detail: 'aggregate' },
  { label: 'SUM()', insertText: 'SUM(${1:column_name}) AS total_amount', detail: 'aggregate' },
  { label: 'AVG()', insertText: 'AVG(${1:column_name}) AS average_value', detail: 'aggregate' },
  { label: 'MIN()', insertText: 'MIN(${1:column})', detail: 'aggregate' },
  { label: 'MAX()', insertText: 'MAX(${1:column})', detail: 'aggregate' },
  {
    label: 'CASE WHEN',
    insertText: 'CASE WHEN ${1:condition} THEN ${2:value} ELSE ${3:other} END',
    detail: 'expression',
  },
]
