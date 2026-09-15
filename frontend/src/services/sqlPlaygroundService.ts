import { apiClient } from '@/api/client'
import { apiEndpoints } from '@/api/config'
import type { SqlRunResponse, SqlTableSchemaPublic } from '@/types/sql'

export interface SqlPlaygroundDatasetSummary {
  id: string
  title: string
  summary: string
  tables: string[]
}

export interface SqlPlaygroundCatalog {
  language: string
  assessed: boolean
  row_limit: number
  timeout_ms: number
  note: string
  datasets: SqlPlaygroundDatasetSummary[]
}

export interface SqlPlaygroundDatasetDetail {
  id: string
  title: string
  summary: string
  documentation: string
  starter_query: string
  assessed: boolean
  row_limit: number
  timeout_ms: number
  tables: Array<
    SqlTableSchemaPublic & {
      sample_columns: string[]
      sample_rows: unknown[][]
      sample_row_count: number
      sample_truncated: boolean
    }
  >
}

export interface SqlPlaygroundRunResponse extends SqlRunResponse {
  assessed: boolean
  row_limit: number
  timeout_ms: number
  note: string
}

export async function fetchSqlPlaygroundCatalog() {
  const { data } = await apiClient.get<SqlPlaygroundCatalog>(apiEndpoints.sql.playground)
  return data
}

export async function fetchSqlPlaygroundDataset(datasetId: string) {
  const { data } = await apiClient.get<SqlPlaygroundDatasetDetail>(
    apiEndpoints.sql.playgroundDataset(datasetId),
  )
  return data
}

export async function runSqlPlaygroundQuery(datasetId: string, query: string) {
  const { data } = await apiClient.post<SqlPlaygroundRunResponse>(
    apiEndpoints.sql.playgroundRun(datasetId),
    { query },
  )
  return data
}
