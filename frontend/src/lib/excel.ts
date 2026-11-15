import type { WorkBook, WorkSheet } from 'xlsx'
import type { CellValue, TableData } from '../types'
import { displayCell, formatNumber, normalizeCell } from './cells'

type XlsxModule = typeof import('xlsx')

let xlsxPromise: Promise<XlsxModule> | null = null
let syncXlsx: XlsxModule | null = null

export function loadXlsx(): Promise<XlsxModule> {
  if (!xlsxPromise) {
    xlsxPromise = import('xlsx').then((module) => {
      syncXlsx = module
      return module
    })
  }
  return xlsxPromise
}

export function isExcelFile(file: File): boolean {
  return /\.(xlsx|xls)$/i.test(file.name)
}

export async function readWorkbook(file: File): Promise<WorkBook> {
  const XLSX = await loadXlsx()
  const buffer = await file.arrayBuffer()
  return XLSX.read(buffer, { type: 'array', cellDates: true })
}

export function getSheetNames(workbook: WorkBook): string[] {
  return workbook.SheetNames.slice()
}

function sheetToGrid(sheet: WorkSheet): CellValue[][] {
  if (!syncXlsx) {
    throw new Error('Excel 引擎尚未加载，请重新选择文件')
  }
  const range = syncXlsx.utils.decode_range(sheet['!ref'] ?? 'A1:A1')
  const width = Math.min(Math.max(range.e.c - range.s.c + 1, 1), 1000)
  const height = Math.max(range.e.r - range.s.r + 1, 1)
  const grid: CellValue[][] = []
  for (let r = 0; r < height; r += 1) {
    const row: CellValue[] = []
    for (let c = 0; c < width; c += 1) {
      const cell = sheet[syncXlsx.utils.encode_cell({ r: range.s.r + r, c: range.s.c + c })]
      row.push(normalizeCell(cell ? cell.v : null))
    }
    grid.push(row)
  }
  return grid
}

export function readGrid(workbook: WorkBook, sheetName: string): CellValue[][] {
  const sheet = workbook.Sheets[sheetName]
  if (!sheet) return []
  return sheetToGrid(sheet)
}

export async function exportTable(table: TableData, fileName: string): Promise<void> {
  const XLSX = await loadXlsx()
  const header = table.columns
  const rows = table.rows.map((row) => header.map((column) => row[column] ?? null))
  const sheet = XLSX.utils.aoa_to_sheet([header, ...rows])
  sheet['!cols'] = header.map((column) => {
    const sampleLengths = table.rows
      .slice(0, 80)
      .map((row) => displayCell(row[column]).length)
    const longest = Math.max(column.length + 2, ...sampleLengths)
    return { wch: Math.min(32, Math.max(8, longest + 2)) }
  })
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, sheet, '数据统计')
  const output = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' })
  const blob = new Blob([output], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function timestampSuffix(date = new Date()): string {
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}_${pad(
    date.getHours(),
  )}${pad(date.getMinutes())}${pad(date.getSeconds())}`
}

export { formatNumber }
