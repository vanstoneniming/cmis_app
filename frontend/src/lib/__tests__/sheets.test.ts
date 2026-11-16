import { describe, expect, it } from 'vitest'
import {
  buildTsv,
  classesOf,
  groupRowsByClass,
  groupRowsBySheet,
  groupRowsForOutput,
  hasSheetInfo,
  safeSheetName,
  tablesBySheet,
} from '../sheets'

describe('groupRowsBySheet', () => {
  it('keeps the import order of the sheets and of the rows inside them', () => {
    expect(groupRowsBySheet(['1班', '2班', '1班'], 3)).toEqual([
      { name: '1班', indices: [0, 2] },
      { name: '2班', indices: [1] },
    ])
  })

  it('falls back to one unnamed group when no sheet info exists', () => {
    expect(groupRowsBySheet([], 2)).toEqual([{ name: '', indices: [0, 1] }])
  })
})

describe('groupRowsByClass', () => {
  it('splits students by class when the session has no sheet info', () => {
    const rows = [
      { 姓名: '张三', 班级: '高一(1)班' },
      { 姓名: '李四', 班级: '高一(2)班' },
      { 姓名: '王五', 班级: '高一(1)班' },
    ]
    expect(groupRowsByClass(rows)).toEqual([
      { name: '高一(1)班', indices: [0, 2] },
      { name: '高一(2)班', indices: [1] },
    ])
  })

  it('keeps rows without a class in their own group', () => {
    expect(groupRowsByClass([{ 姓名: '张三', 班级: '' }])).toEqual([
      { name: '未分班', indices: [0] },
    ])
  })
})

describe('groupRowsForOutput', () => {
  it('prefers the original worksheets and never merges everything into one group', () => {
    expect(hasSheetInfo(['1班', '2班'])).toBe(true)
    expect(hasSheetInfo(['', ''])).toBe(false)
    expect(
      groupRowsForOutput(
        [
          { 姓名: '张三', 班级: 'A班' },
          { 姓名: '李四', 班级: 'B班' },
        ],
        ['工作表1', '工作表2'],
      ),
    ).toEqual([
      { name: '工作表1', indices: [0] },
      { name: '工作表2', indices: [1] },
    ])
    expect(
      groupRowsForOutput(
        [
          { 姓名: '张三', 班级: 'A班' },
          { 姓名: '李四', 班级: 'B班' },
        ],
        ['', ''],
      ),
    ).toEqual([
      { name: 'A班', indices: [0] },
      { name: 'B班', indices: [1] },
    ])
  })
})

describe('tablesBySheet', () => {
  it('splits rows by sheet but keeps every column', () => {
    const rows = [
      { 学号: '1', 姓名: '张三', 期中: 80 },
      { 学号: '2', 姓名: '李四', 期中: 90 },
    ]
    const columns = ['学号', '姓名', '期中']
    const tables = tablesBySheet(columns, rows, ['1班', '2班'])
    expect(tables.map((entry) => entry.name)).toEqual(['1班', '2班'])
    expect(tables[0]?.table.columns).toEqual(columns)
    expect(tables[1]?.table.rows).toEqual([{ 学号: '2', 姓名: '李四', 期中: 90 }])
  })
})

describe('buildTsv', () => {
  it('builds tab separated rows with empty cells kept as placeholders', () => {
    const tsv = buildTsv(
      ['姓名', '期中', '期末'],
      [
        { 姓名: '张三', 期中: 80, 期末: null },
        { 姓名: '李四', 期中: 90, 期末: 88 },
      ],
    )
    expect(tsv).toBe('张三\t80\t\n李四\t90\t88')
  })

  it('replaces tabs and newlines inside a cell so columns stay aligned', () => {
    expect(buildTsv(['备注'], [{ 备注: '第一行\n第二行' }])).toBe('第一行 第二行')
  })
})

describe('safeSheetName', () => {
  it('strips characters Excel forbids and caps the length', () => {
    const used = new Set<string>()
    expect(safeSheetName('高一/1班:[A]', used, '工作表1')).toBe('高一 1班  A')
    const long = safeSheetName('班'.repeat(40), used, '工作表1')
    expect(long.length).toBe(31)
  })

  it('renames duplicates instead of overwriting a sheet', () => {
    const used = new Set<string>()
    expect(safeSheetName('1班', used, '工作表1')).toBe('1班')
    expect(safeSheetName('1班', used, '工作表1')).toBe('1班(2)')
    expect(safeSheetName('1班', used, '工作表1')).toBe('1班(3)')
  })

  it('uses the fallback name for empty sheet names', () => {
    const used = new Set<string>()
    expect(safeSheetName('', used, '数据统计')).toBe('数据统计')
  })
})

describe('classesOf', () => {
  it('lists the classes of a sheet without duplicates', () => {
    expect(
      classesOf([
        { 姓名: '张三', 班级: '高一(1)班' },
        { 姓名: '李四', 班级: '高一(1)班' },
        { 姓名: '王五', 班级: '' },
      ]),
    ).toEqual(['高一(1)班'])
  })
})
