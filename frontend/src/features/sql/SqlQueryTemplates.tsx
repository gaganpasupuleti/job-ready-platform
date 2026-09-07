import { Button } from '@/components/common/Button'
import {
  buildCountTemplate,
  buildGroupByTemplate,
  buildHavingTemplate,
  buildJoinTwoTablesTemplate,
  buildOrderLimitTemplate,
  buildSelectTemplate,
  buildWhereTemplate,
  getDefaultColumnName,
  getDefaultTableName,
} from '@/features/sql/utils/sqlEditorInsert'
import type { SqlTableSchemaPublic } from '@/types/sql'

export type SqlQueryTemplateId =
  | 'select_all'
  | 'where'
  | 'count'
  | 'group_by'
  | 'having'
  | 'join'
  | 'order_limit'

interface SqlQueryTemplatesProps {
  tables: SqlTableSchemaPublic[]
  onInsert: (sql: string, templateId: SqlQueryTemplateId) => void
}

const TEMPLATES: Array<{ id: SqlQueryTemplateId; label: string; tip: string }> = [
  { id: 'select_all', label: 'SELECT *', tip: 'Select all rows from a table' },
  { id: 'where', label: 'WHERE', tip: 'Filter rows with a condition' },
  { id: 'count', label: 'COUNT', tip: 'Count rows in a table' },
  { id: 'group_by', label: 'GROUP BY', tip: 'Group and count by a column' },
  { id: 'having', label: 'HAVING', tip: 'Filter groups after GROUP BY' },
  { id: 'join', label: 'INNER JOIN', tip: 'Join two tables (edit ON keys)' },
  { id: 'order_limit', label: 'ORDER BY + LIMIT', tip: 'Sort and take top N' },
]

export function SqlQueryTemplates({ tables, onInsert }: SqlQueryTemplatesProps) {
  const tableName = getDefaultTableName(tables)
  const table = tables.find((t) => t.table_name === tableName)
  const columnName = getDefaultColumnName(table)
  const secondTable = tables[1]

  const build = (id: SqlQueryTemplateId): string => {
    switch (id) {
      case 'select_all':
        return buildSelectTemplate(tableName)
      case 'where':
        return buildWhereTemplate(tableName, columnName)
      case 'count':
        return buildCountTemplate(tableName)
      case 'group_by':
        return buildGroupByTemplate(tableName, columnName)
      case 'having':
        return buildHavingTemplate(tableName, columnName)
      case 'join':
        if (!secondTable) {
          return buildSelectTemplate(tableName)
        }
        return buildJoinTwoTablesTemplate(
          tableName,
          secondTable.table_name,
          columnName,
          getDefaultColumnName(secondTable),
        )
      case 'order_limit':
        return buildOrderLimitTemplate(tableName, columnName)
    }
  }

  if (!tables.length) return null

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-subtle)]">
        Quick queries
      </p>
      <div className="flex flex-wrap gap-1.5">
        {TEMPLATES.map((tpl) => (
          <Button
            key={tpl.id}
            type="button"
            size="sm"
            variant="secondary"
            title={tpl.tip}
            onClick={() => onInsert(build(tpl.id), tpl.id)}
          >
            {tpl.label}
          </Button>
        ))}
      </div>
    </div>
  )
}
