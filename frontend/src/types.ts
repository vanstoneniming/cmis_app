export type CellValue = string | number | boolean | Date | null

export type DataRow = Record<string, CellValue>

export interface TableData {
  columns: string[]
  rows: DataRow[]
}

export type ColumnKind = 'number' | 'text'

export interface ColumnMeta {
  name: string
  kind: ColumnKind
  numericRatio: number
}

export interface AnalyzedTable {
  table: TableData
  columns: ColumnMeta[]
}

export interface RosterMapping {
  nameCol: string
  idCol: string
  classCol: string
}

export interface RosterDetection {
  table: TableData
  mapping: RosterMapping
  split: { sourceCol: string; nameCol: string; idCol: string } | null
}

export interface DuplicateConflict {
  key: string
  name: string
  scoreRowIndex: number
  scoreRow: DataRow
  candidateIndices: number[]
  preferredIndex?: number
}

export interface MergeOptions {
  base: TableData
  score: TableData
  matchColumn: string
  dataColumns: string[]
  duplicateSelections: Record<string, number>
}

export interface MergeResult {
  table: TableData
  addedColumns: string[]
  renamedColumns: Array<{ from: string; to: string }>
  matchedRows: number
  updatedCells: number
  unmatched: string[]
  error: string | null
}

export interface MergeReport {
  kind: 'roster' | 'merge'
  title: string
  details: string[]
  addedColumns: string[]
  renamedColumns: Array<{ from: string; to: string }>
  unmatched: string[]
}

export const BASE_COLUMNS = ['学号', '姓名', '班级'] as const

export type BaseColumn = (typeof BASE_COLUMNS)[number]
