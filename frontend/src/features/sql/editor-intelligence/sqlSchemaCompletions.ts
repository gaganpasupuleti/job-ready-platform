import type {
  SqlCompletionContext,
  SqlCompletionSchema,
} from '@/features/sql/editor-intelligence/sqlCompletion.types'

export function getTableNames(schema: SqlCompletionSchema): string[] {
  return schema.tables.map((t) => t.name)
}

export function getAllColumnNames(schema: SqlCompletionSchema): string[] {
  const seen = new Set<string>()
  const columns: string[] = []
  for (const table of schema.tables) {
    for (const col of table.columns) {
      if (!seen.has(col.name)) {
        seen.add(col.name)
        columns.push(col.name)
      }
    }
  }
  return columns.sort()
}

export function getColumnsForTable(schema: SqlCompletionSchema, tableName: string): string[] {
  const table = schema.tables.find((t) => t.name.toLowerCase() === tableName.toLowerCase())
  return table?.columns.map((c) => c.name) ?? []
}

export function resolveTableFromQualifier(
  schema: SqlCompletionSchema,
  qualifier: string,
  sqlText: string,
): string | null {
  const direct = schema.tables.find((t) => t.name.toLowerCase() === qualifier.toLowerCase())
  if (direct) return direct.name

  const fromMatch = sqlText.match(
    new RegExp(`\\b(?:FROM|JOIN)\\s+(\\w+)\\s+(?:AS\\s+)?${qualifier}\\b`, 'i'),
  )
  if (fromMatch?.[1]) return fromMatch[1]
  return null
}

export function detectSqlCompletionContext(
  textBeforeCursor: string,
): { context: SqlCompletionContext; tableQualifier?: string } {
  const qualified = /(?:\b(\w+)\.)$/.exec(textBeforeCursor)
  if (qualified) {
    return { context: 'table_qualified', tableQualifier: qualified[1] }
  }

  const trimmed = textBeforeCursor.trimEnd()
  // Keep after_from while the user is typing a partial table name.
  if (/\b(FROM|JOIN)\s+\w*$/i.test(trimmed) || /\b(FROM|JOIN)\s*$/i.test(trimmed)) {
    return { context: 'after_from' }
  }

  const normalized = textBeforeCursor.replace(/\s+/g, ' ').toUpperCase()
  if (/\bSELECT(\s+\w*)?$/.test(normalized) || /,\s*\w*$/.test(textBeforeCursor)) {
    return { context: 'after_select' }
  }
  if (/\bWHERE(\s+\w*)?$/.test(normalized)) {
    return { context: 'after_where' }
  }
  if (/\bGROUP\s+BY(\s+\w*)?$/.test(normalized)) {
    return { context: 'after_group_by' }
  }
  if (/\bORDER\s+BY(\s+\w*)?$/.test(normalized)) {
    return { context: 'after_order_by' }
  }
  if (/\bHAVING(\s+\w*)?$/.test(normalized)) {
    return { context: 'after_having' }
  }
  return { context: 'general' }
}
