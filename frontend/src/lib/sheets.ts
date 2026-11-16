import type { CellValue, DataRow, TableData } from '../types'
import { displayCell } from './cells'

/** 一个工作表（通常对应一个班级）在数据表里占的行 */
export interface SheetGroup {
  name: string
  /** 行在数据表里的下标，保持导入时的顺序 */
  indices: number[]
}

/** 按来源工作表把行分组，组的先后顺序与导入顺序一致。 */
export function groupRowsBySheet(rowSheets: string[], rowCount: number): SheetGroup[] {
  const groups: SheetGroup[] = []
  const byName = new Map<string, SheetGroup>()
  for (let index = 0; index < rowCount; index += 1) {
    const name = rowSheets[index] ?? ''
    let group = byName.get(name)
    if (!group) {
      group = { name, indices: [] }
      byName.set(name, group)
      groups.push(group)
    }
    group.indices.push(index)
  }
  return groups
}

/** 会话里是否真的记录了来源工作表（旧会话没有这个信息）。 */
export function hasSheetInfo(rowSheets: string[]): boolean {
  return rowSheets.some((name) => Boolean(name))
}

/** 没有工作表信息时按班级分组，避免把所有班级混在一次复制/一张表里。 */
export function groupRowsByClass(rows: DataRow[]): SheetGroup[] {
  const groups: SheetGroup[] = []
  const byName = new Map<string, SheetGroup>()
  rows.forEach((row, index) => {
    const name = displayCell(row['班级'] ?? null).trim() || '未分班'
    let group = byName.get(name)
    if (!group) {
      group = { name, indices: [] }
      byName.set(name, group)
      groups.push(group)
    }
    group.indices.push(index)
  })
  return groups
}

/**
 * 复制与导出共用：优先按原文件的工作表拆，没有工作表信息时退回按班级拆。
 * 两种情况都不做「所有学生合成一份」。
 */
export function groupRowsForOutput(rows: DataRow[], rowSheets: string[]): SheetGroup[] {
  if (hasSheetInfo(rowSheets)) return groupRowsBySheet(rowSheets, rows.length)
  return groupRowsByClass(rows)
}

/** 每个工作表单表导出用的数据（列相同，行按工作表切分）。 */
export function tablesBySheet(
  columns: string[],
  rows: DataRow[],
  rowSheets: string[],
): Array<{ name: string; table: TableData }> {
  return tablesForGroups(columns, rows, groupRowsBySheet(rowSheets, rows.length))
}

/** 把已经分好的组转成导出用的表。 */
export function tablesForGroups(
  columns: string[],
  rows: DataRow[],
  groups: SheetGroup[],
): Array<{ name: string; table: TableData }> {
  return groups.map((group) => ({
    name: group.name,
    table: {
      columns: columns.slice(),
      rows: group.indices.map((index) => ({ ...rows[index]! })),
    },
  }))
}

/** 制表符分隔的文本，直接粘进 Excel 会按列拆开。 */
export function buildTsv(columns: string[], rows: DataRow[]): string {
  return rows
    .map((row) => columns.map((column) => tsvCell(row[column] ?? null)).join('\t'))
    .join('\n')
}

function tsvCell(value: CellValue): string {
  // 单元格里的制表符/换行会破坏 Excel 的列对齐，统一换成空格
  return displayCell(value).replace(/[\t\r\n]+/g, ' ')
}

/**
 * Excel 工作表名的限制：最长 31 个字符，不能带 \ / ? * [ ] :，
 * 且同一工作簿内不能重名。
 */
export function safeSheetName(
  name: string,
  used: Set<string>,
  fallback: string,
): string {
  const cleaned = name.replace(/[\\/?*[\]:]/g, ' ').trim().slice(0, 31) || fallback
  let candidate = cleaned
  let counter = 2
  while (used.has(candidate)) {
    const suffix = `(${counter})`
    candidate = `${cleaned.slice(0, Math.max(1, 31 - suffix.length))}${suffix}`
    counter += 1
  }
  used.add(candidate)
  return candidate
}

/** 工作表里出现的班级，用于复制面板上的说明。 */
export function classesOf(rows: DataRow[]): string[] {
  const seen = new Set<string>()
  rows.forEach((row) => {
    const value = displayCell(row['班级'] ?? null).trim()
    if (value) seen.add(value)
  })
  return [...seen]
}
