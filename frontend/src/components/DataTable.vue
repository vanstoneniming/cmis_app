<script setup lang="ts">
import { computed, ref } from 'vue'
import { Download, Layers, Search } from 'lucide-vue-next'
import type { CellValue, DataRow } from '../types'
import { BASE_COLUMNS } from '../types'
import { displayCell, isEmptyCell } from '../lib/cells'
import { useSessionStore } from '../stores/session'

const props = defineProps<{
  columns: string[]
  rows: DataRow[]
}>()

defineEmits<{
  'open-merge': []
  export: []
}>()

const session = useSessionStore()
const query = ref('')
const classFilter = ref('')

const dataColumns = computed(() =>
  props.columns.filter((column) => !(BASE_COLUMNS as readonly string[]).includes(column)),
)

const classOptions = computed(() => {
  const values = new Set<string>()
  props.rows.forEach((row) => {
    const value = displayCell(row['班级'] ?? null).trim()
    if (value) values.add(value)
  })
  return [...values].sort((a, b) => a.localeCompare(b, 'zh-CN'))
})

const filteredEntries = computed(() => {
  const needle = query.value.trim().toLowerCase()
  return props.rows
    .map((row, index) => ({ row, index }))
    .filter(({ row }) => {
      if (classFilter.value && displayCell(row['班级'] ?? null).trim() !== classFilter.value) {
        return false
      }
      if (!needle) return true
      const haystack = [
        displayCell(row['学号'] ?? null),
        displayCell(row['姓名'] ?? null),
        displayCell(row['班级'] ?? null),
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(needle)
    })
})

const columnKinds = computed(() => {
  const map = new Map<string, 'number' | 'text'>()
  dataColumns.value.forEach((column) => {
    const values = props.rows
      .map((row) => row[column] ?? null)
      .filter((value): value is CellValue => !isEmptyCell(value))
    map.set(
      column,
      values.length > 0 && values.every((value) => typeof value === 'number') ? 'number' : 'text',
    )
  })
  return map
})

function inputValue(value: CellValue): string {
  return displayCell(value)
}

function onEdit(index: number, column: string, event: Event) {
  const target = event.target as HTMLInputElement
  const kind = columnKinds.value.get(column) ?? 'text'
  const raw = target.value.trim()
  if (raw === '') {
    session.updateCell(index, column, null)
    return
  }
  if (kind === 'number') {
    const numeric = Number(raw)
    if (Number.isFinite(numeric)) {
      session.updateCell(index, column, numeric)
    } else {
      target.value = ''
      session.updateCell(index, column, null)
    }
    return
  }
  session.updateCell(index, column, raw)
}

function blurTarget(event: Event) {
  ;(event.target as HTMLInputElement).blur()
}
</script>

<template>
  <section class="data-card" data-testid="data-table">
    <div class="table-toolbar">
      <div class="toolbar-title">
        <h2>数据表</h2>
        <span>{{ rows.length }} 名学生 · {{ dataColumns.length }} 个数据列</span>
      </div>
      <div class="toolbar-controls">
        <label class="search-box">
          <Search :size="15" aria-hidden="true" />
          <span class="sr-only">搜索学生</span>
          <input v-model="query" type="search" placeholder="搜索姓名、学号或班级" />
        </label>
        <select v-model="classFilter" class="control class-filter" aria-label="按班级筛选">
          <option value="">全部班级</option>
          <option v-for="className in classOptions" :key="className" :value="className">
            {{ className }}
          </option>
        </select>
        <button class="btn btn-secondary btn-sm" type="button" data-testid="table-export" @click="$emit('export')">
          <Download :size="15" />
          导出
        </button>
        <button
          class="btn btn-primary btn-sm"
          type="button"
          data-testid="table-open-merge"
          @click="$emit('open-merge')"
        >
          <Layers :size="15" />
          导入数据列
        </button>
      </div>
    </div>

    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th class="col-index">#</th>
            <th class="col-id">学号</th>
            <th class="col-name">姓名</th>
            <th class="col-class">班级</th>
            <th
              v-for="column in dataColumns"
              :key="column"
              class="col-data"
              :title="columnKinds.get(column) === 'number' ? '数值列，可直接修改' : '文本列，可直接修改'"
            >
              <span>{{ column }}</span>
              <em v-if="columnKinds.get(column) === 'number'">数值</em>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in filteredEntries" :key="entry.index" :data-testid="`data-row-${entry.index}`">
            <td class="col-index">{{ entry.index + 1 }}</td>
            <td class="col-id">{{ displayCell(entry.row['学号'] ?? null) || '—' }}</td>
            <td class="col-name">{{ displayCell(entry.row['姓名'] ?? null) || '—' }}</td>
            <td class="col-class">
              <span v-if="displayCell(entry.row['班级'] ?? null)" class="class-pill">
                {{ displayCell(entry.row['班级'] ?? null) }}
              </span>
              <span v-else class="muted-dash">—</span>
            </td>
            <td v-for="column in dataColumns" :key="column" class="col-data">
              <input
                class="cell-input"
                :class="{ 'is-number': columnKinds.get(column) === 'number' }"
                :type="columnKinds.get(column) === 'number' ? 'number' : 'text'"
                :step="columnKinds.get(column) === 'number' ? 'any' : undefined"
                :value="inputValue(entry.row[column] ?? null)"
                :aria-label="`${displayCell(entry.row['姓名'] ?? null)}的${column}`"
                :data-testid="`cell-${entry.index}-${column}`"
                @change="onEdit(entry.index, column, $event)"
                @keydown.enter.prevent="blurTarget"
              />
            </td>
          </tr>
          <tr v-if="filteredEntries.length === 0">
            <td :colspan="dataColumns.length + 4" class="empty-row">
              没有匹配的学生，试试清空搜索或切换班级。
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="table-footer">
      <span>共 {{ rows.length }} 名学生，当前显示 {{ filteredEntries.length }} 名</span>
      <span>学号、姓名、班级为基准字段；点击其他单元格即可修改</span>
    </div>
  </section>
</template>

<style scoped>
.data-card {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--line);
  background: var(--surface);
}

.toolbar-title {
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
  min-width: 0;
}

.toolbar-title h2 {
  font-size: 18px;
  white-space: nowrap;
}

.toolbar-title span {
  color: var(--muted);
  font-size: 11.5px;
  white-space: nowrap;
}

.toolbar-controls {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 218px;
  height: 32px;
  padding: 0 0.6rem;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  background: var(--surface);
  color: var(--muted);
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease;
}

.search-box:focus-within {
  border-color: var(--pine-soft);
  box-shadow: 0 0 0 3px rgba(26, 107, 88, 0.1);
}

.search-box input {
  min-width: 0;
  flex: 1;
  padding: 0;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--ink);
  font-size: 12px;
}

.search-box input::placeholder {
  color: #94a29a;
}

.class-filter {
  width: 132px;
  height: 32px;
  padding-left: 0.55rem;
  font-size: 12px;
}

.table-scroll {
  max-height: 64vh;
  overflow: auto;
}

table {
  width: max-content;
  min-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  font-size: 12.5px;
}

th,
td {
  height: 42px;
  padding: 0 0.65rem;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: middle;
  white-space: nowrap;
}

thead th {
  position: sticky;
  top: 0;
  z-index: 4;
  height: 38px;
  background: #f2f6f2;
  color: var(--ink-soft);
  font-size: 11.5px;
  font-weight: 600;
}

thead th.col-data {
  display: table-cell;
}

thead th.col-data em {
  margin-left: 0.35rem;
  color: var(--muted);
  font-size: 9.5px;
  font-style: normal;
  font-weight: 400;
}

tbody tr:hover td {
  background: #fbfcf9;
}

tbody tr:hover .cell-input {
  border-color: var(--line);
  background: #fff;
}

.col-index,
.col-id,
.col-name,
.col-class {
  position: sticky;
  z-index: 2;
  background: var(--surface);
}

thead .col-index,
thead .col-id,
thead .col-name,
thead .col-class {
  z-index: 6;
  background: #f2f6f2;
}

tbody tr:hover .col-index,
tbody tr:hover .col-id,
tbody tr:hover .col-name,
tbody tr:hover .col-class {
  background: #fbfcf9;
}

.col-index {
  left: 0;
  width: 46px;
  min-width: 46px;
  color: var(--muted);
  font-size: 10.5px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.col-id {
  left: 46px;
  width: 126px;
  min-width: 126px;
  font-variant-numeric: tabular-nums;
  color: var(--ink-soft);
}

.col-name {
  left: 172px;
  width: 104px;
  min-width: 104px;
  font-weight: 500;
}

.col-class {
  left: 276px;
  width: 146px;
  min-width: 146px;
  box-shadow: 10px 0 14px -14px rgba(13, 74, 61, 0.4);
}

.col-data {
  width: 132px;
  min-width: 132px;
}

.class-pill {
  display: inline-flex;
  align-items: center;
  height: 22px;
  max-width: 100%;
  padding: 0 0.5rem;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface-soft);
  color: var(--ink-soft);
  font-size: 10.5px;
  text-overflow: ellipsis;
}

.muted-dash {
  color: #a4b0a8;
}

.cell-input {
  width: 100%;
  height: 30px;
  padding: 0 0.45rem;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: var(--ink);
  font-size: 12.5px;
  transition:
    border-color 140ms ease,
    background-color 140ms ease,
    box-shadow 140ms ease;
}

.cell-input:hover {
  border-color: var(--line);
  background: #fff;
}

.cell-input:focus {
  outline: none;
  border-color: var(--pine-soft);
  background: #fff;
  box-shadow: 0 0 0 3px rgba(26, 107, 88, 0.1);
}

.cell-input.is-number {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.empty-row {
  height: 90px;
  color: var(--muted);
  font-size: 12.5px;
  text-align: center;
}

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.55rem 1rem;
  border-top: 1px solid var(--line);
  background: var(--surface-soft);
  color: var(--muted);
  font-size: 10.5px;
}

@media (max-width: 900px) {
  .table-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .toolbar-controls {
    width: 100%;
    justify-content: flex-start;
  }

  .search-box {
    flex: 1;
    width: auto;
    min-width: 160px;
  }
}

@media (max-width: 700px) {
  .col-index {
    width: 38px;
    min-width: 38px;
  }

  .col-name {
    left: 38px;
    width: 92px;
    min-width: 92px;
  }

  .col-id,
  .col-class {
    width: 112px;
    min-width: 112px;
  }

  tbody .col-id,
  tbody .col-class {
    position: static;
  }

  thead .col-id,
  thead .col-class {
    left: auto;
    z-index: 4;
  }

  thead .col-index,
  thead .col-name {
    z-index: 8;
  }

  .col-class {
    box-shadow: none;
  }
}

@media (max-width: 430px) {
  .col-index {
    display: none;
  }

  .col-name {
    left: 0;
  }
}

@media (max-width: 620px) {
  .class-filter {
    width: 120px;
  }

  .table-footer span:last-child {
    display: none;
  }
}
</style>
