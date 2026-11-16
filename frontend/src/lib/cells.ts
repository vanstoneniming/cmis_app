import type { CellValue } from '../types'

const EMPTY_TOKENS = new Set([
  '',
  'nan',
  'none',
  'null',
  'nat',
  '<na>',
  'n/a',
  '#n/a',
  '-',
  '—',
])

export function normalizeCell(value: unknown): CellValue {
  if (value === null || value === undefined) return null
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value
  }
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null
  }
  if (typeof value === 'boolean') return value
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (EMPTY_TOKENS.has(trimmed.toLowerCase())) return null
    return trimmed
  }
  const asString = String(value).trim()
  return asString === '' ? null : asString
}

export function isEmptyCell(value: CellValue): boolean {
  if (value === null || value === undefined) return true
  if (typeof value === 'string') return value.trim() === ''
  if (value instanceof Date) return Number.isNaN(value.getTime())
  return false
}

export function formatDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  const hours = value.getHours()
  const minutes = value.getMinutes()
  if (hours === 0 && minutes === 0) return `${year}-${month}-${day}`
  return `${year}-${month}-${day} ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}

export function formatNumber(value: number): string {
  if (!Number.isFinite(value)) return ''
  if (Number.isInteger(value)) return String(value)
  return String(Math.round(value * 1e6) / 1e6)
}

/** Display a value in tables and messages. */
export function displayCell(value: CellValue): string {
  if (isEmptyCell(value)) return ''
  if (value instanceof Date) return formatDate(value)
  if (typeof value === 'number') return formatNumber(value)
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  return String(value)
}

/** Stable string used for IDs: numeric 2024001 becomes "2024001", not "2024001.0". */
export function idString(value: CellValue): string {
  if (isEmptyCell(value)) return ''
  if (typeof value === 'number') return formatNumber(value)
  if (value instanceof Date) return formatDate(value)
  return String(value).trim()
}

/** String used for matching names or IDs. */
export function matchString(value: CellValue): string {
  return idString(value).normalize('NFKC').replace(/\s+/g, ' ').trim()
}

export function parseNumber(value: CellValue): number | null {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  if (isEmptyCell(value)) return null
  const text = displayCell(value).replace(/[,，\s]/g, '')
  if (text === '') return null
  const parsed = Number(text)
  return Number.isFinite(parsed) ? parsed : null
}

export function isBlankRow(row: CellValue[]): boolean {
  return row.every((cell) => isEmptyCell(cell))
}

export function padNumber(value: number, length: number): string {
  return String(value).padStart(length, '0')
}
