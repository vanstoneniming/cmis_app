import type {
  AnalyzedTable,
  CellValue,
  ColumnMeta,
  DataRow,
  DuplicateConflict,
  MergeOptions,
  MergeResult,
  RosterDetection,
  RosterMapping,
  TableData,
  UnmatchedRow,
} from '../types'
import {
  displayCell,
  idString,
  isBlankRow,
  isEmptyCell,
  matchString,
  normalizeCell,
  padNumber,
  parseNumber,
} from './cells'

const NUMERIC_HEADER = /评分|分数|score|成绩|总分|平均分|数量|count/i
const TEXT_HEADER = /学校|班级|class|school|名称|name|学号|学生编号|考号|编号|备注|remark|note|姓名|名字/i
const ID_HEADER = /学号|学生编号|考号|编号|student[_\s-]?id|(^|[^a-z])id([^a-z]|$)/i
const NAME_HEADER = /姓名|名字|name/i
const CLASS_HEADER = /班级|教学班|行政班|class/i

const HEADER_HINT = /姓名|名字|name|学号|编号|成绩|分数|score/i
const SUMMARY_NAME =
  /^(班级|班别|合计|总计|小计|平均分?|最高分|最低分|及格率|优秀率|标准差|优秀分数|良好分数|及格分数|满分|成绩权值|统计|汇总|备注)([（(].*[)）])?$/

export function looksLikeHeader(row: CellValue[]): boolean {
  return row.some((cell) => HEADER_HINT.test(displayCell(cell)))
}

export function uniqueColumnName(base: string, used: Set<string>): string {
  const cleaned = base.trim() || '列'
  if (!used.has(cleaned)) return cleaned
  let counter = 1
  while (used.has(`${cleaned}_${counter}`)) counter += 1
  return `${cleaned}_${counter}`
}

function dedupeHeaders(headers: string[]): string[] {
  const used = new Set<string>()
  return headers.map((header) => {
    const name = uniqueColumnName(header, used)
    used.add(name)
    return name
  })
}

function pruneEmptyColumns(table: TableData): TableData {
  if (table.columns.length === 0 || table.rows.length === 0) return table
  const keep = table.columns.filter((column) =>
    table.rows.some((row) => !isEmptyCell(row[column])),
  )
  if (keep.length === table.columns.length) return table
  const rows = table.rows.map((row) => {
    const next: DataRow = {}
    keep.forEach((column) => {
      next[column] = row[column]
    })
    return next
  })
  return { columns: keep, rows }
}

export function gridToTable(
  grid: CellValue[][],
  skipRows = 0,
  skipFooter = 0,
): TableData {
  const normalized = grid.map((row) => row.map((cell) => normalizeCell(cell)))
  const start = Math.max(0, Math.min(skipRows, normalized.length))
  const end = Math.max(start, normalized.length - Math.max(0, skipFooter))
  const sliced = normalized.slice(start, end)
  while (sliced.length > 0 && isBlankRow(sliced[sliced.length - 1]!)) {
    sliced.pop()
  }
  if (sliced.length === 0) return { columns: [], rows: [] }

  const width = Math.max(...sliced.map((row) => row.length), 1)
  const firstRow = sliced[0]!
  const useHeader = skipRows === 0 || looksLikeHeader(firstRow)
  const headerCells = useHeader ? firstRow : []
  const dataCells = useHeader ? sliced.slice(1) : sliced

  const rawHeaders = Array.from({ length: width }, (_, index) => {
    if (!useHeader) return `列${index + 1}`
    const text = displayCell(headerCells[index] ?? null).trim()
    return text === '' ? `列${index + 1}` : text
  })
  const columns = dedupeHeaders(rawHeaders)

  const rows: DataRow[] = dataCells.map((cells) => {
    const row: DataRow = {}
    columns.forEach((column, index) => {
      row[column] = normalizeCell(cells[index] ?? null)
    })
    return row
  })

  return pruneEmptyColumns({ columns, rows })
}

function numericRatioFor(values: CellValue[]): number {
  const nonEmpty = values.filter((value) => !isEmptyCell(value)).slice(0, 60)
  if (nonEmpty.length === 0) return 0
  const numeric = nonEmpty.filter((value) => {
    if (typeof value === 'number') return true
    if (value instanceof Date) return false
    return parseNumber(value) !== null
  }).length
  return numeric / nonEmpty.length
}

export function classifyColumn(name: string, values: CellValue[]): ColumnMeta {
  const ratio = numericRatioFor(values)
  if (NUMERIC_HEADER.test(name)) {
    return { name, kind: 'number', numericRatio: ratio }
  }
  if (TEXT_HEADER.test(name) || ID_HEADER.test(name)) {
    return { name, kind: 'text', numericRatio: ratio }
  }
  if (ratio >= 0.7) {
    return { name, kind: 'number', numericRatio: ratio }
  }
  return { name, kind: 'text', numericRatio: ratio }
}

function convertByKind(value: CellValue, kind: 'number' | 'text'): CellValue {
  if (isEmptyCell(value)) return null
  if (kind === 'number') {
    return parseNumber(value)
  }
  return displayCell(value)
}

export function analyzeTable(table: TableData): AnalyzedTable {
  const columns = table.columns.map((column) =>
    classifyColumn(
      column,
      table.rows.map((row) => row[column] ?? null),
    ),
  )
  const kinds = new Map(columns.map((column) => [column.name, column.kind]))
  const rows = table.rows.map((row) => {
    const next: DataRow = {}
    table.columns.forEach((column) => {
      next[column] = convertByKind(row[column] ?? null, kinds.get(column) ?? 'text')
    })
    return next
  })
  return { table: { columns: table.columns.slice(), rows }, columns }
}

export function looksLikeIdColumn(name: string): boolean {
  return ID_HEADER.test(name)
}

export function looksLikeNameColumn(name: string): boolean {
  return NAME_HEADER.test(name)
}

export function looksLikeClassColumn(name: string): boolean {
  return CLASS_HEADER.test(name) || name.trim() === '班'
}

export function matchKindOf(column: string): 'id' | 'name' | 'unsupported' {
  if (looksLikeIdColumn(column)) return 'id'
  if (looksLikeNameColumn(column)) return 'name'
  return 'unsupported'
}

export function classKey(value: CellValue): string {
  const text = displayCell(value).trim()
  if (!text) return ''
  const match = /(\d+)\s*班\s*$/.exec(text)
  if (!match) return text
  const digits = match[1] ?? ''
  const numeric = digits.length > 2 ? digits.slice(-2) : digits
  return String(Number(numeric))
}

export interface MatchCandidate {
  column: string
  kind: 'id' | 'name'
  matches: number
  total: number
  rate: number
}

function matchPriority(column: string): number {
  if (/学号|学生编号|student[\s_-]?id/i.test(column)) return 3
  if (matchKindOf(column) === 'name') return 2
  if (matchKindOf(column) === 'id') return 1
  return 0
}

/** Estimate how many rows of `score` can be matched to the base roster. */
export function scoreMatchColumns(
  base: TableData,
  score: TableData,
  columns: string[],
): MatchCandidate[] {
  const idSet = new Set(
    base.rows.map((row) => matchString(row['学号'] ?? null)).filter(Boolean),
  )
  const nameSet = new Set(
    base.rows.map((row) => matchString(row['姓名'] ?? null)).filter(Boolean),
  )

  return columns.flatMap((column) => {
    const kind = matchKindOf(column)
    if (kind === 'unsupported') return []
    const pool = kind === 'id' ? idSet : nameSet
    let total = 0
    let matches = 0
    for (const row of score.rows.slice(0, 400)) {
      const key = matchString(row[column] ?? null)
      if (!key) continue
      total += 1
      if (pool.has(key)) matches += 1
    }
    return [
      {
        column,
        kind,
        matches,
        total,
        rate: total > 0 ? matches / total : 0,
      },
    ]
  })
}

/** Pick the name/id column with the highest overlap against the base roster. */
export function suggestMatchColumn(
  base: TableData,
  score: TableData,
  columns: string[],
): string {
  const candidates = scoreMatchColumns(base, score, columns)
  if (candidates.length === 0) return columns[0] ?? ''
  const ranked = candidates.slice().sort((a, b) => {
    if (b.rate !== a.rate) return b.rate - a.rate
    const priority = matchPriority(b.column) - matchPriority(a.column)
    if (priority !== 0) return priority
    return columns.indexOf(a.column) - columns.indexOf(b.column)
  })
  return ranked[0]?.column ?? columns[0] ?? ''
}

function detectMapping(table: TableData, split: RosterDetection['split']): RosterMapping {
  let idCol = split?.idCol ?? ''
  let nameCol = split?.nameCol ?? ''
  let classCol = ''

  for (const column of table.columns) {
    if (!idCol && looksLikeIdColumn(column) && !looksLikeClassColumn(column)) {
      idCol = column
    }
    if (!nameCol && looksLikeNameColumn(column)) {
      nameCol = column
    }
    if (!classCol && looksLikeClassColumn(column)) {
      classCol = column
    }
  }

  return { nameCol, idCol, classCol }
}

const COMBINED_NAME_ID = /^(.+?)\s*[（(]\s*(\d+)\s*[)）]$/

export function splitCombinedNameId(table: TableData): {
  table: TableData
  split: RosterDetection['split']
} {
  for (const column of table.columns) {
    const nonEmpty = table.rows
      .map((row) => row[column] ?? null)
      .filter((value) => !isEmptyCell(value))
    if (nonEmpty.length < 2) continue
    let matched = 0
    for (const value of nonEmpty) {
      if (COMBINED_NAME_ID.test(displayCell(value))) matched += 1
    }
    if (matched < 2 || matched <= nonEmpty.length * 0.5) continue

    const used = new Set(table.columns)
    const nameCol = uniqueColumnName(`${column}_姓名`, used)
    used.add(nameCol)
    const idCol = uniqueColumnName(`${column}_学号`, used)
    used.add(idCol)

    const matchedRows = table.rows.map((row) =>
      COMBINED_NAME_ID.test(displayCell(row[column] ?? null)),
    )
    const firstMatch = matchedRows.indexOf(true)
    const lastMatch = matchedRows.lastIndexOf(true)

    const rows = table.rows.map((row, index) => {
      const raw = row[column] ?? null
      const text = displayCell(raw)
      const match = COMBINED_NAME_ID.exec(text)
      const next: DataRow = { ...row }
      if (match) {
        next[nameCol] = normalizeCell(match[1] ?? '')
        next[idCol] = normalizeCell(match[2] ?? '')
      } else if (index > firstMatch && index < lastMatch) {
        // Keep a name without an id only when it sits inside the student block.
        next[nameCol] = raw
        next[idCol] = null
      } else {
        // Titles and summary rows live above/below the combined student block.
        next[nameCol] = null
        next[idCol] = null
      }
      return next
    })

    return {
      table: { columns: [...table.columns, nameCol, idCol], rows },
      split: { sourceCol: column, nameCol, idCol },
    }
  }
  return { table, split: null }
}

/** Split combined name/id columns, type the table, and guess the mapping. */
export function prepareRosterTable(rawTable: TableData): RosterDetection {
  const splitResult = splitCombinedNameId(rawTable)
  const analyzed = analyzeTable(splitResult.table)
  return {
    table: analyzed.table,
    mapping: detectMapping(analyzed.table, splitResult.split),
    split: splitResult.split,
  }
}

export interface BuildStudentsOptions {
  fallbackClass?: string
  startIndex?: number
}

export interface BuildStudentsResult {
  rows: DataRow[]
  nextIndex: number
  warnings: string[]
}

export function buildStudentsFromTable(
  table: TableData,
  mapping: RosterMapping,
  options: BuildStudentsOptions = {},
): BuildStudentsResult {
  const { nameCol, idCol, classCol } = mapping
  if (!nameCol || !table.columns.includes(nameCol)) {
    throw new Error('无法识别姓名列，请在列映射中手动选择')
  }

  const warnings: string[] = []
  const seenIds = new Map<string, number>()
  const rows: DataRow[] = []
  let sequence = options.startIndex ?? 1
  let emitted = 0

  table.rows.forEach((row, rowIndex) => {
    const name = displayCell(row[nameCol] ?? null).trim()
    if (!name) return

    let studentId = idCol && table.columns.includes(idCol) ? idString(row[idCol] ?? null).trim() : ''
    const summaryCandidate = name.replace(/[:：]+$/, '').trim()
    if (!studentId && SUMMARY_NAME.test(summaryCandidate)) return

    const className =
      classCol && table.columns.includes(classCol)
        ? displayCell(row[classCol] ?? null).trim()
        : (options.fallbackClass ?? '').trim()

    if (!studentId) {
      const serial = sequence + emitted
      studentId = className
        ? `${className}_${padNumber(serial, 3)}`
        : `STU_${padNumber(serial, 4)}`
    }

    const normalizedId = matchString(studentId)
    if (normalizedId) {
      const previous = seenIds.get(normalizedId)
      if (previous !== undefined) {
        warnings.push(`学号「${studentId}」重复（第 ${previous + 1} 行与第 ${rowIndex + 1} 行）`)
      } else {
        seenIds.set(normalizedId, rowIndex)
      }
    }

    rows.push({
      学号: studentId,
      姓名: name,
      班级: className,
    })
    emitted += 1
  })

  return { rows, nextIndex: sequence + emitted, warnings: warnings.slice(0, 20) }
}

export type MatchKind = 'id' | 'name' | 'unsupported'

export function conflictKey(name: string, rowIndex: number): string {
  return `${name}\u0000${rowIndex}`
}

export function computeDuplicateConflicts(
  base: TableData,
  score: TableData,
  matchColumn: string,
): DuplicateConflict[] {
  if (matchKindOf(matchColumn) !== 'name') return []
  if (!base.columns.includes('姓名')) return []

  const byName = new Map<string, number[]>()
  base.rows.forEach((row, index) => {
    const name = matchString(row['姓名'] ?? null)
    if (!name) return
    const list = byName.get(name)
    if (list) list.push(index)
    else byName.set(name, [index])
  })

  const classColumn = score.columns.find(
    (column) => looksLikeClassColumn(column) && column !== matchColumn,
  )
  const conflicts: DuplicateConflict[] = []
  score.rows.forEach((row, rowIndex) => {
    const name = matchString(row[matchColumn] ?? null)
    if (!name) return
    const candidates = byName.get(name)
    if (!candidates || candidates.length <= 1) return

    const scoreClass = classColumn ? classKey(row[classColumn] ?? null) : ''
    const classMatches = scoreClass
      ? candidates.filter(
          (index) => classKey(base.rows[index]?.['班级'] ?? null) === scoreClass,
        )
      : []

    conflicts.push({
      key: conflictKey(name, rowIndex),
      name,
      scoreRowIndex: rowIndex,
      scoreRow: { ...row },
      candidateIndices: candidates.slice(),
      preferredIndex: classMatches.length === 1 ? classMatches[0] : undefined,
    })
  })
  return conflicts
}

const PRIMARY_SCORE_HEADER = /总分|总成绩|成绩|得分|分数|score|total/i

/** Sensible initial data columns: primary score columns, or a small set of numbers. */
export function defaultMergeColumns(
  columns: ColumnMeta[],
  matchColumn: string,
): string[] {
  const numeric = columns.filter(
    (column) => column.name !== matchColumn && column.kind === 'number',
  )
  const primary = numeric.filter((column) => PRIMARY_SCORE_HEADER.test(column.name))
  if (primary.length > 0) return primary.map((column) => column.name)
  if (numeric.length > 0 && numeric.length <= 8) {
    return numeric.map((column) => column.name)
  }
  return []
}

export function dataColumnsOf(columns: string[]): string[] {
  return columns.filter((column) => !['学号', '姓名', '班级'].includes(column))
}

export function completenessOf(table: TableData): number | null {
  const dataColumns = dataColumnsOf(table.columns)
  if (dataColumns.length === 0 || table.rows.length === 0) return null
  let filled = 0
  const total = dataColumns.length * table.rows.length
  table.rows.forEach((row) => {
    dataColumns.forEach((column) => {
      if (!isEmptyCell(row[column] ?? null)) filled += 1
    })
  })
  return total === 0 ? null : filled / total
}

function convertMergedValue(value: CellValue, kind: 'number' | 'text'): CellValue {
  if (isEmptyCell(value)) return null
  if (kind === 'number') {
    const numeric = parseNumber(value)
    return numeric === null ? displayCell(value) : numeric
  }
  return displayCell(value)
}

export interface MergeOptionsWithMeta extends MergeOptions {
  scoreColumns: ColumnMeta[]
}

/** 未匹配行的中文原因，弹窗与报告横幅共用 */
export function describeUnmatchedRow(row: UnmatchedRow): string {
  if (row.reason === 'ambiguous') {
    return `同名学生 ${row.candidates} 人，未指定对应记录`
  }
  return row.matchedKind === 'id' ? '基准名单中没有该学号' : '基准名单中没有该姓名'
}

export function mergeData(options: MergeOptionsWithMeta): MergeResult {
  const {
    base,
    score,
    scoreColumns,
    matchColumn,
    dataColumns,
    duplicateSelections,
  } = options
  const unmatched: string[] = []
  const unmatchedRows: UnmatchedRow[] = []

  const matchKind = matchKindOf(matchColumn)
  if (!matchColumn || !score.columns.includes(matchColumn)) {
    return {
      table: base,
      addedColumns: [],
      renamedColumns: [],
      matchedRows: 0,
      updatedCells: 0,
      unmatched: [],
      unmatchedRows: [],
      error: '请选择用于匹配的列',
    }
  }
  if (matchKind === 'unsupported') {
    return {
      table: base,
      addedColumns: [],
      renamedColumns: [],
      matchedRows: 0,
      updatedCells: 0,
      unmatched: [],
      unmatchedRows: [],
      error: '匹配列需要是姓名或学号类列，请重新选择',
    }
  }
  if (dataColumns.length === 0) {
    return {
      table: base,
      addedColumns: [],
      renamedColumns: [],
      matchedRows: 0,
      updatedCells: 0,
      unmatched: [],
      unmatchedRows: [],
      error: '请至少选择一个要并入的数据列',
    }
  }

  const nameColumn = score.columns.find((column) => matchKindOf(column) === 'name') ?? ''
  const idColumn = score.columns.find((column) => matchKindOf(column) === 'id') ?? ''
  const classColumn =
    score.columns.find((column) => looksLikeClassColumn(column)) ?? ''
  const identityOf = (row: DataRow, value: CellValue) => ({
    name: nameColumn
      ? displayCell(row[nameColumn] ?? null)
      : matchKind === 'name'
        ? displayCell(value)
        : '',
    className: classColumn ? displayCell(row[classColumn] ?? null) : '',
    studentId: idColumn
      ? displayCell(row[idColumn] ?? null)
      : matchKind === 'id'
        ? displayCell(value)
        : '',
  })

  const table: TableData = {
    columns: base.columns.slice(),
    rows: base.rows.map((row) => ({ ...row })),
  }

  const used = new Set(table.columns)
  const finalNames = new Map<string, string>()
  const addedColumns: string[] = []
  const renamedColumns: Array<{ from: string; to: string }> = []

  dataColumns.forEach((column) => {
    const finalName = uniqueColumnName(column, used)
    used.add(finalName)
    finalNames.set(column, finalName)
    addedColumns.push(finalName)
    if (finalName !== column) renamedColumns.push({ from: column, to: finalName })
    if (!table.columns.includes(finalName)) {
      table.columns.push(finalName)
      table.rows.forEach((row) => {
        row[finalName] = null
      })
    }
  })

  const kindByColumn = new Map(scoreColumns.map((column) => [column.name, column.kind]))
  const idIndex = new Map<string, number[]>()
  const nameIndex = new Map<string, number[]>()
  if (table.columns.includes('学号')) {
    table.rows.forEach((row, index) => {
      const key = matchString(row['学号'] ?? null)
      if (!key) return
      const list = idIndex.get(key)
      if (list) list.push(index)
      else idIndex.set(key, [index])
    })
  }
  if (table.columns.includes('姓名')) {
    table.rows.forEach((row, index) => {
      const key = matchString(row['姓名'] ?? null)
      if (!key) return
      const list = nameIndex.get(key)
      if (list) list.push(index)
      else nameIndex.set(key, [index])
    })
  }

  const matched = new Set<number>()
  let updatedCells = 0

  score.rows.forEach((row, rowIndex) => {
    const value = row[matchColumn] ?? null
    const key = matchString(value)
    if (!key) return

    const candidates =
      matchKind === 'id' ? (idIndex.get(key) ?? []) : (nameIndex.get(key) ?? [])

    if (candidates.length === 0) {
      if (unmatched.length < 200) {
        const matchedValue = displayCell(value)
        unmatched.push(
          `第 ${rowIndex + 1} 行：未找到${matchKind === 'id' ? '学号' : '姓名'}「${matchedValue}」`,
        )
        unmatchedRows.push({
          rowNumber: rowIndex + 1,
          matchedKind: matchKind,
          matchedValue,
          ...identityOf(row, value),
          reason: 'not-found',
          candidates: 0,
        })
      }
      return
    }

    let target = candidates[0]!
    if (candidates.length > 1) {
      const selected = duplicateSelections[conflictKey(key, rowIndex)]
      if (selected === undefined || !candidates.includes(selected)) {
        if (unmatched.length < 200) {
          const matchedValue = displayCell(value)
          unmatched.push(
            `第 ${rowIndex + 1} 行：「${matchedValue}」有 ${candidates.length} 个同名学生，请选择对应记录`,
          )
          unmatchedRows.push({
            rowNumber: rowIndex + 1,
            matchedKind: matchKind,
            matchedValue,
            ...identityOf(row, value),
            reason: 'ambiguous',
            candidates: candidates.length,
          })
        }
        return
      }
      target = selected
    }

    matched.add(rowIndex)
    dataColumns.forEach((column) => {
      const finalName = finalNames.get(column)
      if (!finalName) return
      const kind = kindByColumn.get(column) ?? 'text'
      const converted = convertMergedValue(row[column] ?? null, kind)
      table.rows[target]![finalName] = converted
      if (!isEmptyCell(converted)) updatedCells += 1
    })
  })

  return {
    table,
    addedColumns,
    renamedColumns,
    matchedRows: matched.size,
    updatedCells,
    unmatched,
    unmatchedRows,
    error: null,
  }
}
