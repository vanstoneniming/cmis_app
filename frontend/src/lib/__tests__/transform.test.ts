import { describe, expect, it } from 'vitest'
import type { DataRow, TableData } from '../../types'
import {
  analyzeTable,
  buildStudentsFromTable,
  completenessOf,
  computeDuplicateConflicts,
  defaultMergeColumns,
  gridToTable,
  mergeData,
  prepareRosterTable,
  scoreMatchColumns,
  suggestMatchColumn,
} from '../transform'

const rosterGrid = [
  ['学号', '姓名', '班级'],
  ['2024001', '张三', '高一(1)班'],
  ['2024002', '李四', '高一(1)班'],
  ['2024006', '张三', '高一(2)班'],
]

function studentRows(): DataRow[] {
  const prepared = prepareRosterTable(gridToTable(rosterGrid))
  return buildStudentsFromTable(prepared.table, prepared.mapping).rows
}

describe('gridToTable', () => {
  it('uses the first row as the header and skips footer rows', () => {
    const table = gridToTable(
      [
        ['学号', '姓名', '班级'],
        ['2024001', '张三', '1班'],
        ['2024002', '李四', '1班'],
        ['合计', '', ''],
      ],
      0,
      1,
    )
    expect(table.columns).toEqual(['学号', '姓名', '班级'])
    expect(table.rows).toHaveLength(2)
    expect(table.rows[1]?.['姓名']).toBe('李四')
  })

  it('detects a header after skipped title rows and deduplicates columns', () => {
    const table = gridToTable(
      [
        ['2025 学年名单'],
        ['学号', '姓名', '姓名'],
        ['2024001', '张三', '张三'],
      ],
      1,
      0,
    )
    expect(table.columns).toEqual(['学号', '姓名', '姓名_1'])
    expect(table.rows).toHaveLength(1)
  })

  it('keeps class-like numbers as text but converts score columns to numbers', () => {
    const analyzed = analyzeTable(
      gridToTable(
        [
          ['学号', '姓名', '班级', '期中'],
          ['001', '张三', '1', '85.5'],
        ],
        0,
        0,
      ),
    )
    expect(analyzed.table.rows[0]?.['学号']).toBe('001')
    expect(analyzed.table.rows[0]?.['班级']).toBe('1')
    expect(analyzed.table.rows[0]?.['期中']).toBe(85.5)
  })
})

describe('roster detection', () => {
  it('splits a combined name and id column', () => {
    const prepared = prepareRosterTable(
      gridToTable(
        [
          ['学生信息', '班级'],
          ['张三 (2024001)', '1班'],
          ['李四 (2024002)', '1班'],
        ],
        0,
        0,
      ),
    )
    expect(prepared.split?.sourceCol).toBe('学生信息')
    expect(prepared.mapping.nameCol).toContain('姓名')
    expect(prepared.mapping.idCol).toContain('学号')
    expect(prepared.mapping.classCol).toBe('班级')
  })

  it('generates stable ids when the roster has no id column', () => {
    const prepared = prepareRosterTable(
      gridToTable(
        [
          ['姓名', '班级'],
          ['张三', '1班'],
          ['李四', '1班'],
        ],
        0,
        0,
      ),
    )
    const built = buildStudentsFromTable(prepared.table, prepared.mapping)
    expect(built.rows[0]?.['学号']).toBe('1班_001')
    expect(built.rows[1]?.['学号']).toBe('1班_002')
  })
})

describe('mergeData', () => {
  it('merges selected columns by student id and renames duplicate columns', () => {
    const base: TableData = { columns: ['学号', '姓名', '班级', '期中'], rows: studentRows() }
    base.rows[0]!['期中'] = 70
    const analyzed = analyzeTable(
      gridToTable(
        [
          ['学号', '期中', '期末'],
          ['2024002', 76, 88],
          ['2024001', 84, 91],
        ],
        0,
        0,
      ),
    )
    const result = mergeData({
      base,
      score: analyzed.table,
      scoreColumns: analyzed.columns,
      matchColumn: '学号',
      dataColumns: ['期中', '期末'],
      duplicateSelections: {},
    })
    expect(result.error).toBeNull()
    expect(result.matchedRows).toBe(2)
    expect(result.renamedColumns).toEqual([{ from: '期中', to: '期中_1' }])
    expect(result.table.rows[0]?.['期中_1']).toBe(84)
    expect(result.table.rows[0]?.['期末']).toBe(91)
    expect(result.table.rows[1]?.['期末']).toBe(88)
  })

  it('requires a selection when a name matches more than one student', () => {
    const base: TableData = { columns: ['学号', '姓名', '班级'], rows: studentRows() }
    const analyzed = analyzeTable(
      gridToTable(
        [
          ['姓名', '期中'],
          ['张三', 80],
          ['张三', 90],
        ],
        0,
        0,
      ),
    )
    const conflicts = computeDuplicateConflicts(base, analyzed.table, '姓名')
    expect(conflicts).toHaveLength(2)
    expect(conflicts[0]?.candidateIndices).toEqual([0, 2])

    const missing = mergeData({
      base,
      score: analyzed.table,
      scoreColumns: analyzed.columns,
      matchColumn: '姓名',
      dataColumns: ['期中'],
      duplicateSelections: {},
    })
    expect(missing.matchedRows).toBe(0)
    expect(missing.unmatched).toHaveLength(2)

    const selections = {
      [conflicts[0]!.key]: 0,
      [conflicts[1]!.key]: 2,
    }
    const resolved = mergeData({
      base,
      score: analyzed.table,
      scoreColumns: analyzed.columns,
      matchColumn: '姓名',
      dataColumns: ['期中'],
      duplicateSelections: selections,
    })
    expect(resolved.matchedRows).toBe(2)
    expect(resolved.table.rows[0]?.['期中']).toBe(80)
    expect(resolved.table.rows[2]?.['期中']).toBe(90)
  })

  it('rejects a match column that is neither name nor id', () => {
    const analyzed = analyzeTable(
      gridToTable(
        [
          ['班级', '期中'],
          ['1班', 80],
        ],
        0,
        0,
      ),
    )
    const result = mergeData({
      base: { columns: ['学号', '姓名', '班级'], rows: studentRows() },
      score: analyzed.table,
      scoreColumns: analyzed.columns,
      matchColumn: '班级',
      dataColumns: ['期中'],
      duplicateSelections: {},
    })
    expect(result.error).toContain('姓名或学号')
  })
})

describe('completenessOf', () => {
  it('reports filled data cells', () => {
    const table: TableData = {
      columns: ['学号', '姓名', '班级', '期中', '期末'],
      rows: [
        { 学号: '1', 姓名: '张三', 班级: '1班', 期中: 80, 期末: null },
        { 学号: '2', 姓名: '李四', 班级: '1班', 期中: 90, 期末: 70 },
      ],
    }
    expect(completenessOf(table)).toBe(0.75)
  })
})

describe('real-world grade sheet rows', () => {
  it('drops rows above and below the combined name-id student block', () => {
    const prepared = prepareRosterTable(
      gridToTable(
        [
          ['序号', '学生'],
          ['班级：', ''],
          ['1', '张三 (2024001)'],
          ['2', '李四 (2024002)'],
          ['3', '王五 (2024003)'],
          ['4', '赵六 (2024004)'],
          ['', '优秀分数'],
          ['', '满分'],
        ],
        0,
        0,
      ),
    )
    const built = buildStudentsFromTable(prepared.table, prepared.mapping)
    expect(prepared.split).not.toBeNull()
    expect(built.rows).toHaveLength(4)
    expect(built.rows.map((row) => row['姓名'])).toEqual(['张三', '李四', '王五', '赵六'])
    expect(built.rows.map((row) => row['学号'])).toEqual([
      '2024001',
      '2024002',
      '2024003',
      '2024004',
    ])
  })

  it('skips summary labels when the name column has no id', () => {
    const prepared = prepareRosterTable(
      gridToTable(
        [
          ['姓名', '分数'],
          ['张三', 80],
          ['优秀分数', 51],
          ['满分', 60],
        ],
        0,
        0,
      ),
    )
    const built = buildStudentsFromTable(prepared.table, prepared.mapping)
    expect(built.rows).toHaveLength(1)
    expect(built.rows[0]?.['姓名']).toBe('张三')
  })
})

describe('match suggestions and defaults', () => {
  it('prefers the column with the highest overlap, not just the first id column', () => {
    const base: TableData = {
      columns: ['学号', '姓名', '班级'],
      rows: [
        { 学号: '19129052', 姓名: '韩涵', 班级: '初中部-2028级-7年级-1班' },
        { 学号: '19151969', 姓名: '曹一航', 班级: '初中部-2028级-7年级-1班' },
      ],
    }
    const score: TableData = {
      columns: ['姓名', '考号', '总分'],
      rows: [
        { 姓名: '韩涵', 考号: '20250101', 总分: 39 },
        { 姓名: '曹一航', 考号: '20250102', 总分: 44 },
      ],
    }
    const candidates = scoreMatchColumns(base, score, ['姓名', '考号'])
    expect(candidates.find((candidate) => candidate.column === '姓名')?.matches).toBe(2)
    expect(candidates.find((candidate) => candidate.column === '考号')?.matches).toBe(0)
    expect(suggestMatchColumn(base, score, ['姓名', '考号'])).toBe('姓名')
  })

  it('prefers an explicit student id when both id and name match fully', () => {
    const base: TableData = {
      columns: ['学号', '姓名', '班级'],
      rows: [{ 学号: '2024001', 姓名: '张三', 班级: '1班' }],
    }
    const score: TableData = {
      columns: ['学号', '姓名', '总分'],
      rows: [{ 学号: '2024001', 姓名: '张三', 总分: 88 }],
    }
    expect(suggestMatchColumn(base, score, ['学号', '姓名'])).toBe('学号')
  })

  it('uses the class column to preselect the right duplicate', () => {
    const base: TableData = {
      columns: ['学号', '姓名', '班级'],
      rows: [
        { 学号: '1', 姓名: '张一诺', 班级: '初中部-2028级-7年级-4班' },
        { 学号: '2', 姓名: '张一诺', 班级: '初中部-2028级-7年级-5班' },
      ],
    }
    const score: TableData = {
      columns: ['姓名', '班级', '总分'],
      rows: [
        { 姓名: '张一诺', 班级: '704班', 总分: 44 },
        { 姓名: '张一诺', 班级: '705班', 总分: 47 },
      ],
    }
    const conflicts = computeDuplicateConflicts(base, score, '姓名')
    expect(conflicts.map((conflict) => conflict.preferredIndex)).toEqual([0, 1])
  })

  it('only preselects the total-score column in a wide item-score sheet', () => {
    const columns = [
      { name: '姓名', kind: 'text' as const, numericRatio: 0 },
      { name: '总分', kind: 'number' as const, numericRatio: 1 },
      ...Array.from({ length: 10 }, (_, index) => ({
        name: String(index + 1),
        kind: 'number' as const,
        numericRatio: 1,
      })),
    ]
    expect(defaultMergeColumns(columns, '姓名')).toEqual(['总分'])
  })
})
