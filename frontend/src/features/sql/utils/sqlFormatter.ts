const SQL_KEYWORDS = new Set([
  'SELECT',
  'FROM',
  'WHERE',
  'JOIN',
  'INNER',
  'LEFT',
  'RIGHT',
  'OUTER',
  'FULL',
  'CROSS',
  'ON',
  'GROUP',
  'BY',
  'HAVING',
  'ORDER',
  'LIMIT',
  'OFFSET',
  'AS',
  'AND',
  'OR',
  'NOT',
  'IN',
  'IS',
  'NULL',
  'LIKE',
  'BETWEEN',
  'DISTINCT',
  'COUNT',
  'SUM',
  'AVG',
  'MIN',
  'MAX',
  'ASC',
  'DESC',
  'UNION',
  'ALL',
  'EXISTS',
  'CASE',
  'WHEN',
  'THEN',
  'ELSE',
  'END',
  'WITH',
])

const MAJOR_CLAUSES: Array<{ pattern: RegExp; replacement: string }> = [
  { pattern: /\s+GROUP\s+BY\s+/gi, replacement: '\nGROUP BY ' },
  { pattern: /\s+ORDER\s+BY\s+/gi, replacement: '\nORDER BY ' },
  { pattern: /\s+LEFT\s+OUTER\s+JOIN\s+/gi, replacement: '\nLEFT OUTER JOIN ' },
  { pattern: /\s+RIGHT\s+OUTER\s+JOIN\s+/gi, replacement: '\nRIGHT OUTER JOIN ' },
  { pattern: /\s+INNER\s+JOIN\s+/gi, replacement: '\nINNER JOIN ' },
  { pattern: /\s+LEFT\s+JOIN\s+/gi, replacement: '\nLEFT JOIN ' },
  { pattern: /\s+RIGHT\s+JOIN\s+/gi, replacement: '\nRIGHT JOIN ' },
  { pattern: /\s+FULL\s+OUTER\s+JOIN\s+/gi, replacement: '\nFULL OUTER JOIN ' },
  { pattern: /\s+CROSS\s+JOIN\s+/gi, replacement: '\nCROSS JOIN ' },
  { pattern: /\s+JOIN\s+/gi, replacement: '\nJOIN ' },
  { pattern: /\s+FROM\s+/gi, replacement: '\nFROM ' },
  { pattern: /\s+WHERE\s+/gi, replacement: '\nWHERE ' },
  { pattern: /\s+HAVING\s+/gi, replacement: '\nHAVING ' },
  { pattern: /\s+LIMIT\s+/gi, replacement: '\nLIMIT ' },
]

type StringToken = { type: 'str'; value: string }
type TextToken = { type: 'text'; value: string }

function tokenizeOutsideStrings(sql: string): Array<StringToken | TextToken> {
  const tokens: Array<StringToken | TextToken> = []
  let i = 0
  let text = ''

  const flushText = () => {
    if (text) {
      tokens.push({ type: 'text', value: text })
      text = ''
    }
  }

  while (i < sql.length) {
    if (sql[i] === "'") {
      flushText()
      let j = i + 1
      while (j < sql.length) {
        if (sql[j] === "'" && sql[j + 1] === "'") {
          j += 2
          continue
        }
        if (sql[j] === "'") break
        j++
      }
      tokens.push({ type: 'str', value: sql.slice(i, j + 1) })
      i = j + 1
      continue
    }
    text += sql[i]
    i++
  }

  flushText()
  return tokens
}

function normalizeOperators(segment: string): string {
  return segment
    .replace(/\s*>=\s*/g, ' >= ')
    .replace(/\s*<=\s*/g, ' <= ')
    .replace(/\s*<>\s*/g, ' <> ')
    .replace(/\s*!=\s*/g, ' != ')
    .replace(/([^!<>=])\s*=\s*/g, '$1 = ')
    .replace(/([^<])\s*>\s*(?!=)/g, '$1 > ')
    .replace(/([^>])\s*<\s*(?!=)/g, '$1 < ')
    .replace(/\s*,\s*/g, ', ')
    .replace(/\s*;\s*/g, ';')
    .replace(/\s+/g, ' ')
    .trim()
}

function uppercaseKeywords(segment: string): string {
  return segment.replace(/\b[a-zA-Z_][a-zA-Z0-9_]*\b/g, (word) => {
    const upper = word.toUpperCase()
    return SQL_KEYWORDS.has(upper) ? upper : word
  })
}

function applyMajorClauses(segment: string): string {
  let result = segment
  for (const clause of MAJOR_CLAUSES) {
    result = result.replace(clause.pattern, clause.replacement)
  }
  return result.replace(/\s+ON\s+/gi, ' ON ')
}

function formatTextSegment(segment: string): string {
  let formatted = normalizeOperators(segment)
  formatted = uppercaseKeywords(formatted)
  formatted = applyMajorClauses(formatted)
  formatted = formatted.replace(/^\s*SELECT\s+/i, 'SELECT ')
  return formatted
}

function joinFormattedTokens(tokens: Array<StringToken | TextToken>): string {
  let formatted = ''
  for (const token of tokens) {
    if (token.type === 'str' && formatted.length > 0 && !/\s$/.test(formatted)) {
      formatted += ' '
    }
    formatted += token.type === 'str' ? token.value : formatTextSegment(token.value)
  }
  return formatted
}

function collapseBlankLines(sql: string): string {
  return sql
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n[ \t]+/g, '\n')
    .trim()
}

export function formatSqlQuery(sql: string): string {
  try {
    const trimmed = sql.trim()
    if (!trimmed) return sql

    const tokens = tokenizeOutsideStrings(trimmed)
    const formatted = joinFormattedTokens(tokens)
    const withSelectLine = formatted.replace(/SELECT\s+/i, 'SELECT ')
    return collapseBlankLines(withSelectLine)
  } catch {
    return sql
  }
}
