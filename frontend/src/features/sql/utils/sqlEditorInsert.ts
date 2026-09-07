import type { SqlTableSchemaPublic } from '@/types/sql'

export interface SqlInsertResult {
  text: string
  cursorOffset: number
}

export function insertSnippetAtCursor(
  currentSql: string,
  snippet: string,
  cursorPosition?: number,
): SqlInsertResult {
  const pos = Math.max(0, Math.min(cursorPosition ?? currentSql.length, currentSql.length))
  const before = currentSql.slice(0, pos)
  const after = currentSql.slice(pos)

  const trimmedBefore = before.trimEnd()
  const needsGap = trimmedBefore.length > 0 && !before.endsWith('\n')
  const prefix = needsGap ? '\n\n' : ''

  const text = `${before}${prefix}${snippet}${after}`
  const cursorOffset = before.length + prefix.length + snippet.length
  return { text, cursorOffset }
}

export function buildSelectTemplate(tableName: string): string {
  return `SELECT *\nFROM ${tableName}\nLIMIT 10;`
}

export function buildCountTemplate(tableName: string): string {
  return `SELECT COUNT(*) AS total_count\nFROM ${tableName};`
}

export function buildWhereTemplate(tableName: string, columnName: string): string {
  return `SELECT *\nFROM ${tableName}\nWHERE ${columnName} = 'value'\nLIMIT 10;`
}

export function buildGroupByTemplate(tableName: string, columnName: string): string {
  return `SELECT ${columnName}, COUNT(*) AS total_count\nFROM ${tableName}\nGROUP BY ${columnName}\nORDER BY total_count DESC;`
}

export function buildHavingTemplate(tableName: string, groupColumn: string): string {
  return `SELECT ${groupColumn}, COUNT(*) AS total_count\nFROM ${tableName}\nGROUP BY ${groupColumn}\nHAVING COUNT(*) > 1\nORDER BY total_count DESC;`
}

export function buildOrderLimitTemplate(tableName: string, columnName: string): string {
  return `SELECT *\nFROM ${tableName}\nORDER BY ${columnName}\nLIMIT 10;`
}

export function buildJoinTwoTablesTemplate(
  fromTable: string,
  toTable: string,
  fromColumn: string,
  toColumn: string,
): string {
  return `SELECT *\nFROM ${fromTable}\nJOIN ${toTable}\nON ${fromTable}.${fromColumn} = ${toTable}.${toColumn}\nLIMIT 10;`
}

export function getDefaultTableName(tables: SqlTableSchemaPublic[]): string {
  return tables[0]?.table_name ?? 'table_name'
}

export function getDefaultColumnName(table: SqlTableSchemaPublic | undefined): string {
  if (!table?.columns.length) return 'column_name'
  return table.columns[0].column_name
}

export function buildColumnSnippet(columnName: string): string {
  return columnName
}
