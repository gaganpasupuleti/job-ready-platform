export type SqlCompletionContext =
  | 'general'
  | 'after_select'
  | 'after_from'
  | 'after_join'
  | 'after_where'
  | 'after_group_by'
  | 'after_order_by'
  | 'after_having'
  | 'table_qualified'

export interface SqlKeywordCompletion {
  label: string
  insertText?: string
  detail?: string
}

export interface SqlSnippetCompletion {
  label: string
  filterText?: string
  insertText: string
  detail?: string
  documentation?: string
}

/** Minimal schema shape for completions — adapted from Job Ready SqlTableSchemaPublic. */
export interface SqlCompletionSchema {
  tables: Array<{
    name: string
    columns: Array<{ name: string }>
  }>
}
