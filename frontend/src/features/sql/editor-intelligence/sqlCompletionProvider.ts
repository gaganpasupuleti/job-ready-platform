import type { Monaco } from '@monaco-editor/react'
import type {
  IDisposable,
  IPosition,
  Position,
  editor,
  languages,
} from 'monaco-editor'

import type {
  SqlCompletionContext,
  SqlCompletionSchema,
} from '@/features/sql/editor-intelligence/sqlCompletion.types'
import {
  SQL_AGGREGATE_COMPLETIONS,
  SQL_KEYWORDS,
} from '@/features/sql/editor-intelligence/sqlKeywordCompletions'
import {
  detectSqlCompletionContext,
  getAllColumnNames,
  getColumnsForTable,
  getTableNames,
  resolveTableFromQualifier,
} from '@/features/sql/editor-intelligence/sqlSchemaCompletions'
import { SQL_SNIPPET_COMPLETIONS } from '@/features/sql/editor-intelligence/sqlSnippetCompletions'
import type { SqlTableSchemaPublic } from '@/types/sql'

function matchesPrefix(label: string, prefix: string): boolean {
  if (!prefix) return true
  return label.toLowerCase().includes(prefix.toLowerCase())
}

function buildRange(model: editor.ITextModel, position: IPosition) {
  const word = model.getWordUntilPosition(position)
  return {
    startLineNumber: position.lineNumber,
    endLineNumber: position.lineNumber,
    startColumn: word.startColumn,
    endColumn: word.endColumn,
  }
}

function keywordItems(
  monaco: Monaco,
  items: { label: string; insertText?: string; detail?: string }[],
  prefix: string,
  range: languages.CompletionItem['range'],
  sortPrefix: string,
): languages.CompletionItem[] {
  return items
    .filter((item) => matchesPrefix(item.label, prefix))
    .map((item) => ({
      label: item.label,
      kind: monaco.languages.CompletionItemKind.Keyword,
      insertText: item.insertText ?? item.label,
      insertTextRules: item.insertText?.includes('${')
        ? monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
        : undefined,
      detail: item.detail,
      range,
      sortText: `${sortPrefix}_${item.label}`,
    }))
}

function schemaItems(
  monaco: Monaco,
  names: string[],
  prefix: string,
  range: languages.CompletionItem['range'],
  kind: 'table' | 'column',
  sortPrefix: string,
): languages.CompletionItem[] {
  const itemKind =
    kind === 'table'
      ? monaco.languages.CompletionItemKind.Class
      : monaco.languages.CompletionItemKind.Field
  return names
    .filter((name) => matchesPrefix(name, prefix))
    .map((name) => ({
      label: name,
      kind: itemKind,
      insertText: name,
      detail: kind === 'table' ? 'table' : 'column',
      range,
      sortText: `${sortPrefix}_${name}`,
    }))
}

function snippetItems(
  monaco: Monaco,
  prefix: string,
  range: languages.CompletionItem['range'],
): languages.CompletionItem[] {
  return SQL_SNIPPET_COMPLETIONS.filter(
    (s) => matchesPrefix(s.filterText ?? s.label, prefix) || matchesPrefix(s.label, prefix),
  ).map((s) => ({
    label: s.label,
    kind: monaco.languages.CompletionItemKind.Snippet,
    insertText: s.insertText,
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    detail: s.detail,
    documentation: s.documentation,
    range,
    sortText: `2_${s.label}`,
  }))
}

function suggestionsForContext(
  monaco: Monaco,
  schema: SqlCompletionSchema,
  context: SqlCompletionContext,
  prefix: string,
  range: languages.CompletionItem['range'],
  sqlText: string,
  tableQualifier?: string,
): languages.CompletionItem[] {
  if (context === 'table_qualified' && tableQualifier) {
    const tableName = resolveTableFromQualifier(schema, tableQualifier, sqlText)
    const columns = tableName
      ? getColumnsForTable(schema, tableName)
      : getAllColumnNames(schema)
    return schemaItems(monaco, columns, prefix, range, 'column', '0')
  }

  if (context === 'after_from' || context === 'after_join') {
    return [
      ...schemaItems(monaco, getTableNames(schema), prefix, range, 'table', '0'),
      ...keywordItems(monaco, SQL_KEYWORDS, prefix, range, '3'),
    ]
  }

  if (
    context === 'after_where' ||
    context === 'after_group_by' ||
    context === 'after_order_by' ||
    context === 'after_having'
  ) {
    return [
      ...schemaItems(monaco, getAllColumnNames(schema), prefix, range, 'column', '0'),
      ...keywordItems(monaco, SQL_KEYWORDS, prefix, range, '3'),
    ]
  }

  if (context === 'after_select') {
    return [
      ...schemaItems(monaco, getAllColumnNames(schema), prefix, range, 'column', '0'),
      ...keywordItems(monaco, SQL_AGGREGATE_COMPLETIONS, prefix, range, '1'),
      ...keywordItems(monaco, SQL_KEYWORDS, prefix, range, '3'),
    ]
  }

  return [
    ...keywordItems(monaco, SQL_AGGREGATE_COMPLETIONS, prefix, range, '1'),
    ...snippetItems(monaco, prefix, range),
    ...schemaItems(monaco, getTableNames(schema), prefix, range, 'table', '2'),
    ...schemaItems(monaco, getAllColumnNames(schema), prefix, range, 'column', '2'),
    ...keywordItems(monaco, SQL_KEYWORDS, prefix, range, '3'),
  ]
}

export function toCompletionSchema(tables: SqlTableSchemaPublic[]): SqlCompletionSchema {
  return {
    tables: tables.map((t) => ({
      name: t.table_name,
      columns: t.columns.map((c) => ({ name: c.column_name })),
    })),
  }
}

export function registerSqlCompletionProvider(
  monaco: Monaco,
  tables: SqlTableSchemaPublic[],
): IDisposable {
  const schema = toCompletionSchema(tables)
  return monaco.languages.registerCompletionItemProvider('sql', {
    triggerCharacters: ['.', ' ', '\n', ','],
    provideCompletionItems: (model: editor.ITextModel, position: Position) => {
      const range = buildRange(model, position)
      const prefix = model.getWordUntilPosition(position).word
      const line = model.getLineContent(position.lineNumber)
      const textBeforeCursor = line.slice(0, position.column - 1)
      const { context, tableQualifier } = detectSqlCompletionContext(textBeforeCursor)

      return {
        suggestions: suggestionsForContext(
          monaco,
          schema,
          context,
          prefix,
          range,
          model.getValue(),
          tableQualifier,
        ),
      }
    },
  })
}
