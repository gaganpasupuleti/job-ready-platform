import type { SqlSnippetCompletion } from '@/features/sql/editor-intelligence/sqlCompletion.types'

export const SQL_SNIPPET_COMPLETIONS: SqlSnippetCompletion[] = [
  {
    label: 'select-star-limit',
    filterText: 'SELECT * FROM table LIMIT 10',
    insertText: 'SELECT *\nFROM ${1:table}\nLIMIT 10;',
    detail: 'snippet',
    documentation: 'SELECT * FROM table LIMIT 10;',
  },
  {
    label: 'select-column-where',
    filterText: 'SELECT column_name FROM table_name WHERE',
    insertText: 'SELECT ${1:column_name}\nFROM ${2:table_name}\nWHERE ${3:condition};',
    detail: 'snippet',
    documentation: 'SELECT column_name FROM table_name WHERE condition;',
  },
  {
    label: 'inner-join',
    filterText: 'INNER JOIN',
    insertText:
      'SELECT ${1:a.column}\nFROM ${2:table_a} a\nINNER JOIN ${3:table_b} b ON a.${4:id} = b.${5:id};',
    detail: 'snippet',
    documentation: 'INNER JOIN template',
  },
  {
    label: 'group-by',
    filterText: 'GROUP BY',
    insertText:
      'SELECT ${1:column}, COUNT(*) AS row_count\nFROM ${2:table}\nGROUP BY ${1:column};',
    detail: 'snippet',
    documentation: 'GROUP BY template',
  },
  {
    label: 'having-count',
    filterText: 'HAVING COUNT',
    insertText:
      'SELECT ${1:column}, COUNT(*) AS row_count\nFROM ${2:table}\nGROUP BY ${1:column}\nHAVING COUNT(*) > 1;',
    detail: 'snippet',
    documentation: 'HAVING COUNT(*) > 1 template',
  },
]
