import { defineStore } from 'pinia'
import type { CellValue, DataRow, MergeReport, TableData } from '../types'
import { BASE_COLUMNS } from '../types'
import { completenessOf, dataColumnsOf } from '../lib/transform'
import { isEmptyCell } from '../lib/cells'
import { groupRowsForOutput, hasSheetInfo, tablesForGroups } from '../lib/sheets'

const STORAGE_KEY = 'cmis-app:session:v1'

interface StoredSession {
  columns: string[]
  rows: DataRow[]
  /** 每行来自哪个工作表；旧会话没有这个字段 */
  rowSheets?: string[]
  rosterFileName: string
  rosterLoadedAt: string
  report: MergeReport | null
}

function isStoredSession(value: unknown): value is StoredSession {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Partial<StoredSession>
  return (
    Array.isArray(candidate.columns) &&
    candidate.columns.every((column) => typeof column === 'string') &&
    Array.isArray(candidate.rows) &&
    candidate.rows.every((row) => row && typeof row === 'object' && !Array.isArray(row))
  )
}

/** 行与工作表名一一对应，长度不一致时按空工作表补齐，避免错位。 */
function alignSheets(rowSheets: string[] | undefined, rowCount: number): string[] {
  return Array.from({ length: rowCount }, (_, index) => rowSheets?.[index] ?? '')
}

export const useSessionStore = defineStore('session', {
  state: () => ({
    columns: [] as string[],
    rows: [] as DataRow[],
    /** 与 rows 平行：每行来自基础文件的哪个工作表 */
    rowSheets: [] as string[],
    rosterFileName: '',
    rosterLoadedAt: '',
    report: null as MergeReport | null,
    hydrated: false,
  }),
  getters: {
    hasData: (state) => state.rows.length > 0 && state.columns.length > 0,
    studentCount: (state) => state.rows.length,
    classCount: (state) =>
      new Set(
        state.rows
          .map((row) => row['班级'])
          .filter((value): value is CellValue => !isEmptyCell(value ?? null))
          .map((value) => String(value).trim())
          .filter(Boolean),
      ).size,
    dataColumns: (state) => dataColumnsOf(state.columns),
    completeness: (state): number | null =>
      completenessOf({ columns: state.columns, rows: state.rows }),
    table: (state): TableData => ({ columns: state.columns, rows: state.rows }),
    /** 导入的基础文件是否带来了工作表信息 */
    hasSheetInfo: (state) => hasSheetInfo(state.rowSheets),
    /** 按来源工作表分组；旧会话没有工作表信息时按班级分组 */
    sheetGroups: (state) => groupRowsForOutput(state.rows, state.rowSheets),
    /** 导出用：每个工作表一张表 */
    sheetTables: (state) =>
      tablesForGroups(
        state.columns,
        state.rows,
        groupRowsForOutput(state.rows, state.rowSheets),
      ),
  },
  actions: {
    hydrate() {
      if (this.hydrated) return
      this.hydrated = true
      try {
        const raw = sessionStorage.getItem(STORAGE_KEY)
        if (!raw) return
        const parsed: unknown = JSON.parse(raw)
        if (!isStoredSession(parsed)) return
        const columns = parsed.columns.slice()
        BASE_COLUMNS.forEach((base) => {
          if (!columns.includes(base)) columns.push(base)
        })
        const rows = parsed.rows.map((row) => {
          const next: DataRow = {}
          columns.forEach((column) => {
            const value = row[column]
            next[column] = value === undefined ? null : (value as CellValue)
          })
          return next
        })
        this.columns = columns
        this.rows = rows
        this.rowSheets = alignSheets(parsed.rowSheets, rows.length)
        this.rosterFileName = parsed.rosterFileName ?? ''
        this.rosterLoadedAt = parsed.rosterLoadedAt ?? ''
        this.report = parsed.report ?? null
      } catch {
        // A broken session should never block a fresh import.
      }
    },
    setRoster(
      rows: DataRow[],
      meta: { fileName: string; loadedAt?: string; sheets?: string[] },
    ) {
      this.columns = [...BASE_COLUMNS]
      this.rows = rows.map((row) => ({ ...row }))
      this.rowSheets = alignSheets(meta.sheets, rows.length)
      this.rosterFileName = meta.fileName
      this.rosterLoadedAt = meta.loadedAt ?? new Date().toISOString()
      this.report = null
    },
    replaceTable(table: TableData) {
      this.columns = table.columns.slice()
      this.rows = table.rows.map((row) => ({ ...row }))
      this.rowSheets = alignSheets(this.rowSheets, this.rows.length)
    },
    updateCell(index: number, column: string, value: CellValue) {
      const row = this.rows[index]
      if (!row) return
      row[column] = value
    },
    setReport(report: MergeReport | null) {
      this.report = report
    },
    dismissReport() {
      this.report = null
    },
    clear() {
      this.columns = []
      this.rows = []
      this.rowSheets = []
      this.rosterFileName = ''
      this.rosterLoadedAt = ''
      this.report = null
      try {
        sessionStorage.removeItem(STORAGE_KEY)
      } catch {
        // Storage can be disabled; the in-memory state is already cleared.
      }
    },
    persist() {
      if (!this.hasData) {
        try {
          sessionStorage.removeItem(STORAGE_KEY)
        } catch {
          // ignore
        }
        return
      }
      const payload: StoredSession = {
        columns: this.columns,
        rows: this.rows,
        rowSheets: this.rowSheets,
        rosterFileName: this.rosterFileName,
        rosterLoadedAt: this.rosterLoadedAt,
        report: this.report,
      }
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
      } catch {
        // Quota errors are non-fatal: data still lives in memory.
      }
    },
  },
})
