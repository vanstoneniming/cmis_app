import { defineStore } from 'pinia'
import type { CellValue, DataRow, MergeReport, TableData } from '../types'
import { BASE_COLUMNS } from '../types'
import { completenessOf, dataColumnsOf } from '../lib/transform'
import { isEmptyCell } from '../lib/cells'

const STORAGE_KEY = 'cmis-app:session:v1'

interface StoredSession {
  columns: string[]
  rows: DataRow[]
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

export const useSessionStore = defineStore('session', {
  state: () => ({
    columns: [] as string[],
    rows: [] as DataRow[],
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
        this.rosterFileName = parsed.rosterFileName ?? ''
        this.rosterLoadedAt = parsed.rosterLoadedAt ?? ''
        this.report = parsed.report ?? null
      } catch {
        // A broken session should never block a fresh import.
      }
    },
    setRoster(rows: DataRow[], meta: { fileName: string; loadedAt?: string }) {
      this.columns = [...BASE_COLUMNS]
      this.rows = rows.map((row) => ({ ...row }))
      this.rosterFileName = meta.fileName
      this.rosterLoadedAt = meta.loadedAt ?? new Date().toISOString()
      this.report = null
    },
    replaceTable(table: TableData) {
      this.columns = table.columns.slice()
      this.rows = table.rows.map((row) => ({ ...row }))
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
