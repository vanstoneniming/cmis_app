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

/** 未匹配原因：基准名单里没有，或同名学生没指定对应记录 */
export type UnmatchedReason = 'not-found' | 'ambiguous'

/** 一条没写进名单的成绩行，用于结果页逐条展示 */
export interface UnmatchedRow {
  /** 成绩表里的数据行号（从 1 开始，不含表头与跳过的行） */
  rowNumber: number
  /** 这一行按什么匹配：姓名或学号 */
  matchedKind: 'name' | 'id'
  /** 匹配列里的原始值 */
  matchedValue: string
  name: string
  /** 成绩表里的班级列，没有则为空 */
  className: string
  studentId: string
  reason: UnmatchedReason
  /** 同名学生数量，reason 为 ambiguous 时有意义 */
  candidates: number
}

export interface MergeResult {
  table: TableData
  addedColumns: string[]
  renamedColumns: Array<{ from: string; to: string }>
  matchedRows: number
  updatedCells: number
  unmatched: string[]
  unmatchedRows: UnmatchedRow[]
  error: string | null
}

export interface MergeReport {
  kind: 'roster' | 'merge'
  title: string
  details: string[]
  addedColumns: string[]
  renamedColumns: Array<{ from: string; to: string }>
  unmatched: string[]
  /** 旧会话里持久化的报告可能没有该字段 */
  unmatchedRows?: UnmatchedRow[]
}

export const BASE_COLUMNS = ['学号', '姓名', '班级'] as const

export type BaseColumn = (typeof BASE_COLUMNS)[number]
