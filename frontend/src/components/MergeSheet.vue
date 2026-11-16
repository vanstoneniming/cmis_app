<script setup lang="ts">
import { computed, ref, shallowRef, watch } from 'vue'
import type { WorkBook } from 'xlsx'
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  Loader2,
  Sparkles,
} from 'lucide-vue-next'
import type {
  ColumnMeta,
  DataRow,
  DuplicateConflict,
  MergeReport,
  MergeResult,
  TableData,
} from '../types'
import { displayCell } from '../lib/cells'
import { downloadCsv } from '../lib/csv'
import { getSheetNames, readGrid, readWorkbook, timestampSuffix } from '../lib/excel'
import type { MatchCandidate } from '../lib/transform'
import {
  analyzeTable,
  computeDuplicateConflicts,
  defaultMergeColumns,
  describeUnmatchedRow,
  gridToTable,
  matchKindOf,
  mergeData,
  scoreMatchColumns,
  suggestMatchColumn,
} from '../lib/transform'
import { useSessionStore } from '../stores/session'
import BaseSheet from './BaseSheet.vue'
import FileDropzone from './FileDropzone.vue'
import PreviewTable from './PreviewTable.vue'

const emit = defineEmits<{
  close: []
  imported: [report: MergeReport]
}>()

const session = useSessionStore()

const workbook = shallowRef<WorkBook | null>(null)
const sheetNames = ref<string[]>([])
const selectedSheet = ref('')
const currentFileName = ref('')
const skipRows = ref(0)
const skipFooter = ref(0)
const isLoading = ref(false)
const errorMessage = ref('')
const matchCol = ref('')
const selectedCols = ref<string[]>([])
const selectionTouched = ref(false)
const duplicateSelections = ref<Record<string, number>>({})
const lastResult = ref<MergeResult | null>(null)
/** 结果页关闭时才写入会话报告，避免报告出现在弹窗背后的页面上 */
const pendingReport = ref<MergeReport | null>(null)
/** 导入前的名单快照，用于“撤销本次导入” */
const previousTable = ref<TableData | null>(null)
const undoNotice = ref('')

const baseTable = computed<TableData>(() => ({
  columns: session.columns.slice(),
  rows: session.rows,
}))

const rawTable = computed<TableData>(() => {
  if (!workbook.value || !selectedSheet.value) return { columns: [], rows: [] }
  return gridToTable(
    readGrid(workbook.value, selectedSheet.value),
    Math.max(0, Number(skipRows.value) || 0),
    Math.max(0, Number(skipFooter.value) || 0),
  )
})

const analysis = computed(() => analyzeTable(rawTable.value))
const scoreTable = computed(() => analysis.value.table)
const scoreColumns = computed(() => analysis.value.columns)
const selectedSet = computed(() => new Set(selectedCols.value))
const matchKind = computed(() => matchKindOf(matchCol.value))
const matchCandidates = computed<MatchCandidate[]>(() =>
  scoreMatchColumns(
    baseTable.value,
    scoreTable.value,
    scoreColumns.value.map((column) => column.name),
  ),
)
const currentMatchStat = computed(
  () => matchCandidates.value.find((candidate) => candidate.column === matchCol.value) ?? null,
)
const suggestedMatch = computed<MatchCandidate | null>(() => {
  const suggestedColumn = suggestMatchColumn(
    baseTable.value,
    scoreTable.value,
    scoreColumns.value.map((column) => column.name),
  )
  if (!suggestedColumn || suggestedColumn === matchCol.value) return null
  const target = matchCandidates.value.find((candidate) => candidate.column === suggestedColumn)
  if (!target) return null
  const current = currentMatchStat.value
  if (current && target.rate <= current.rate) return null
  return target
})
const matchSummaryClass = computed(() => {
  const current = currentMatchStat.value
  if (!current || current.total === 0 || current.matches === 0) return 'tag-seal'
  if (current.rate < 0.5) return 'tag-amber'
  return 'tag-green'
})
const matchSummaryText = computed(() => {
  const current = currentMatchStat.value
  if (!current || current.total === 0) return '没有可匹配的数据'
  return `可匹配 ${current.matches} / ${current.total} 行`
})
const matchHint = computed(() => {
  if (!matchCol.value) return '选择用于匹配的列。'
  if (matchKind.value === 'id') return '按学号/考号精确匹配；基准名单中没有的记录会自动忽略。'
  if (matchKind.value === 'name') {
    return '按姓名匹配；重名会要求逐条选择，基准名单中没有的记录会自动忽略。'
  }
  return '当前列不是姓名或学号类列，无法用于匹配，请重新选择。'
})
const matchTag = computed(() => {
  if (matchKind.value === 'id') return '按学号匹配'
  if (matchKind.value === 'name') return '按姓名匹配'
  return '不可用于匹配'
})

const dataOptions = computed(() => {
  const options = scoreColumns.value.filter((column) => column.name !== matchCol.value)
  return [
    ...options.filter((column) => column.kind === 'number'),
    ...options.filter((column) => column.kind === 'text'),
  ]
})

const numericOptions = computed(() =>
  dataOptions.value.filter((column) => column.kind === 'number'),
)

const conflicts = computed(() =>
  computeDuplicateConflicts(baseTable.value, scoreTable.value, matchCol.value),
)

const conflictGroups = computed(() => {
  const groups = new Map<string, DuplicateConflict[]>()
  conflicts.value.forEach((conflict) => {
    const list = groups.get(conflict.name)
    if (list) list.push(conflict)
    else groups.set(conflict.name, [conflict])
  })
  return [...groups.entries()].map(([name, groupConflicts]) => ({
    name,
    conflicts: groupConflicts,
  }))
})

const autoMatchedConflicts = computed(
  () => conflicts.value.filter((conflict) => conflict.preferredIndex !== undefined).length,
)
const duplicateHint = computed(() => {
  if (conflicts.value.length === 0) return ''
  if (autoMatchedConflicts.value === conflicts.value.length) {
    return '系统已按班级自动对应，请核对后再导入。'
  }
  if (autoMatchedConflicts.value > 0) {
    return '系统已按班级预选部分记录，其余请手动选择。'
  }
  return '系统已默认选择第一位，请逐条确认后再导入。'
})

const conflictColumns = computed(() => {
  const preferred = [matchCol.value, ...selectedCols.value].filter(Boolean)
  const fallback = scoreTable.value.columns.slice(0, 6)
  return [...new Set([...(preferred.length ? preferred : fallback), ...fallback])].slice(0, 8)
})

const canImport = computed(
  () =>
    Boolean(workbook.value) &&
    scoreColumns.value.length > 0 &&
    Boolean(matchCol.value) &&
    matchKind.value !== 'unsupported' &&
    selectedCols.value.length > 0,
)

const unmatchedRows = computed(() => lastResult.value?.unmatchedRows ?? [])
const resultDetails = computed(() =>
  lastResult.value?.addedColumns.length
    ? `新增列：${lastResult.value.addedColumns.join('、')}`
    : '没有新增列，只更新了已有列',
)

function applyColumnDefaults(columns: ColumnMeta[]) {
  if (columns.length === 0) {
    matchCol.value = ''
    selectedCols.value = []
    return
  }
  const names = new Set(columns.map((column) => column.name))
  if (!names.has(matchCol.value)) {
    matchCol.value =
      suggestMatchColumn(
        baseTable.value,
        scoreTable.value,
        columns.map((column) => column.name),
      ) ||
      columns[0]?.name ||
      ''
  }
  selectedCols.value = selectedCols.value.filter(
    (column) => names.has(column) && column !== matchCol.value,
  )
  if (!selectionTouched.value) {
    selectedCols.value = defaultMergeColumns(columns, matchCol.value)
  }
}

watch(scoreColumns, (columns) => applyColumnDefaults(columns), { immediate: true })

watch(matchCol, (value, previous) => {
  if (value === previous) return
  selectedCols.value = selectedCols.value.filter((column) => column !== value)
  if (!selectionTouched.value) {
    selectedCols.value = defaultMergeColumns(scoreColumns.value, value)
  }
  duplicateSelections.value = {}
  lastResult.value = null
})

watch(
  conflicts,
  (list) => {
    const validKeys = new Set(list.map((conflict) => conflict.key))
    const next = { ...duplicateSelections.value }
    Object.keys(next).forEach((key) => {
      if (!validKeys.has(key)) delete next[key]
    })
    list.forEach((conflict) => {
      const current = next[conflict.key]
      if (current === undefined || !conflict.candidateIndices.includes(current)) {
        next[conflict.key] = conflict.preferredIndex ?? conflict.candidateIndices[0]!
      }
    })
    duplicateSelections.value = next
  },
  { immediate: true },
)

watch(selectedSheet, () => {
  matchCol.value = ''
  selectedCols.value = []
  selectionTouched.value = false
  duplicateSelections.value = {}
  lastResult.value = null
  pendingReport.value = null
  previousTable.value = null
  errorMessage.value = ''
  applyColumnDefaults(scoreColumns.value)
})

async function loadFile(file: File) {
  isLoading.value = true
  errorMessage.value = ''
  workbook.value = null
  sheetNames.value = []
  currentFileName.value = ''
  selectedSheet.value = ''
  lastResult.value = null
  pendingReport.value = null
  previousTable.value = null
  undoNotice.value = ''
  try {
    const parsed = await readWorkbook(file)
    workbook.value = parsed
    sheetNames.value = getSheetNames(parsed)
    currentFileName.value = file.name
    selectedSheet.value = sheetNames.value[0] ?? ''
    skipRows.value = 0
    skipFooter.value = 0
    matchCol.value = ''
    selectedCols.value = []
    selectionTouched.value = false
    duplicateSelections.value = {}
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? `读取文件失败：${error.message}` : '读取文件失败，请检查文件格式'
  } finally {
    isLoading.value = false
  }
}

function onFileError(message: string) {
  errorMessage.value = message
}

function toggleColumn(name: string) {
  selectionTouched.value = true
  lastResult.value = null
  if (selectedSet.value.has(name)) {
    selectedCols.value = selectedCols.value.filter((column) => column !== name)
  } else {
    selectedCols.value = [...selectedCols.value, name]
  }
}

function selectNumericColumns() {
  selectionTouched.value = true
  lastResult.value = null
  selectedCols.value = numericOptions.value.map((column) => column.name)
}

function clearColumns() {
  selectionTouched.value = true
  lastResult.value = null
  selectedCols.value = []
}

function candidateLabel(index: number): string {
  const row = baseTable.value.rows[index]
  if (!row) return '未知学生'
  const studentId = displayCell(row['学号'] ?? null) || '无学号'
  const className = displayCell(row['班级'] ?? null)
  return className ? `${studentId} · ${className}` : studentId
}

function useSuggestedMatch() {
  if (suggestedMatch.value) matchCol.value = suggestedMatch.value.column
}

function doImport() {
  errorMessage.value = ''
  // 结果页不允许再次导入：数据已经写入，重复提交会二次合并
  if (!canImport.value || lastResult.value) return

  const result = mergeData({
    base: {
      columns: session.columns.slice(),
      rows: session.rows.map((row) => ({ ...row })),
    },
    score: scoreTable.value,
    scoreColumns: scoreColumns.value,
    matchColumn: matchCol.value,
    dataColumns: selectedCols.value,
    duplicateSelections: duplicateSelections.value,
  })

  if (result.error) {
    errorMessage.value = result.error
    return
  }

  if (result.matchedRows === 0) {
    errorMessage.value = suggestedMatch.value
      ? `当前匹配列没有匹配到基准名单中的学生。建议改用「${suggestedMatch.value.column}」（可匹配 ${suggestedMatch.value.matches} / ${suggestedMatch.value.total} 行）。`
      : '当前匹配列没有匹配到基准名单中的学生，请检查匹配列或名单内容。'
    return
  }

  previousTable.value = {
    columns: session.columns.slice(),
    rows: session.rows.map((row) => ({ ...row })),
  }
  session.replaceTable(result.table)
  lastResult.value = result
  undoNotice.value = ''

  const ignored = result.unmatchedRows.length
  pendingReport.value = {
    kind: 'merge',
    title: `已按基准名单导入 ${result.matchedRows} 行成绩`,
    details: [
      `更新 ${result.updatedCells} 个数据单元格`,
      `新增 ${result.addedColumns.length} 个数据列`,
      ...(ignored > 0 ? [`跳过 ${ignored} 行未匹配记录`] : []),
    ],
    addedColumns: result.addedColumns,
    renamedColumns: result.renamedColumns,
    unmatched: result.unmatched,
    unmatchedRows: result.unmatchedRows,
  }
}

/** 写入会话报告并通知外层，只在关闭结果页时执行一次 */
function commitReport() {
  if (!pendingReport.value) return
  session.setReport(pendingReport.value)
  emit('imported', pendingReport.value)
  pendingReport.value = null
}

function finish() {
  commitReport()
  emit('close')
}

function handleSheetClose() {
  // 结果页按 X / Esc / 点遮罩都视为“完成”：数据已写入，不存在取消
  commitReport()
  emit('close')
}

function undoImport() {
  if (!previousTable.value) return
  session.replaceTable(previousTable.value)
  previousTable.value = null
  lastResult.value = null
  pendingReport.value = null
  undoNotice.value = '已撤销本次导入，名单恢复到导入前的状态。可以调整设置后重新导入。'
}

function exportUnmatched() {
  if (!lastResult.value) return
  const header = ['行号', '姓名', '班级', '学号', '未匹配原因']
  const rows = lastResult.value.unmatchedRows.map((row) => [
    String(row.rowNumber),
    row.name || '—',
    row.className || '—',
    row.studentId || '—',
    describeUnmatchedRow(row),
  ])
  downloadCsv(`未匹配学生_${timestampSuffix()}.csv`, header, rows)
}

function visibleValue(row: DataRow, column: string): string {
  return displayCell(row[column] ?? null) || '—'
}
</script>

<template>
  <BaseSheet
    title="合并数据列"
    :subtitle="
      lastResult
        ? '数据已写入当前名单，核对下面的结果后点「完成」回到数据表。'
        : '从第二份 Excel 中选择需要并入的列，按姓名或学号匹配到基准名单。'
    "
    test-id="merge-sheet"
    @close="handleSheetClose"
  >
    <div v-if="undoNotice" class="callout callout-success merge-undo" role="status">
      <CheckCircle2 :size="17" />
      {{ undoNotice }}
    </div>

    <template v-if="lastResult">
      <section class="merge-result" data-testid="merge-result">
        <div class="result-head">
          <span class="result-icon"><CheckCircle2 :size="22" /></span>
          <div>
            <strong>导入完成，已写入当前名单</strong>
            <p>
              按「{{ matchCol }}」匹配到 {{ lastResult.matchedRows }} 名学生；{{ resultDetails }}。
            </p>
            <p class="result-meta">
              {{ currentFileName }}
              <template v-if="selectedSheet"> · 工作表「{{ selectedSheet }}」</template>
            </p>
          </div>
        </div>

        <div class="result-stats">
          <div class="result-stat">
            <span>匹配导入</span>
            <strong>{{ lastResult.matchedRows }}<em>行</em></strong>
          </div>
          <div class="result-stat">
            <span>更新单元格</span>
            <strong>{{ lastResult.updatedCells }}<em>个</em></strong>
          </div>
          <div class="result-stat">
            <span>新增数据列</span>
            <strong>{{ lastResult.addedColumns.length }}<em>列</em></strong>
          </div>
          <div class="result-stat" :class="{ 'is-warn': unmatchedRows.length > 0 }">
            <span>未匹配</span>
            <strong>{{ unmatchedRows.length }}<em>行</em></strong>
          </div>
        </div>

        <p class="result-note">
          点「完成」回到数据表。如果这份文件选错了，用「撤销本次导入」可以恢复导入前的名单。
        </p>
      </section>

      <section v-if="lastResult.addedColumns.length" class="result-block">
        <h4>新增的数据列</h4>
        <div class="result-columns">
          <span v-for="column in lastResult.addedColumns" :key="column" class="tag tag-green">
            {{ column }}
          </span>
        </div>
      </section>

      <details
        v-if="unmatchedRows.length > 0"
        class="unmatched-block"
        open
        data-testid="merge-unmatched"
      >
        <summary>
          <span>未匹配的 {{ unmatchedRows.length }} 行没有写进名单</span>
          <span class="unmatched-toggle">展开 / 收起</span>
        </summary>
        <p class="unmatched-lead">
          这些行在基准名单里找不到对应学生，或同名学生没有指定对应记录。需要保留的话，先导出再在
          Excel 里处理；确认无误后点「完成」。
        </p>
        <div class="unmatched-table-wrap">
          <table class="unmatched-table">
            <thead>
              <tr>
                <th scope="col">行号</th>
                <th scope="col">姓名</th>
                <th scope="col">班级</th>
                <th scope="col">学号</th>
                <th scope="col">未匹配原因</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in unmatchedRows"
                :key="`${row.rowNumber}-${row.matchedValue}-${row.reason}`"
              >
                <td class="num">{{ row.rowNumber }}</td>
                <td>{{ row.name || '—' }}</td>
                <td>{{ row.className || '—' }}</td>
                <td class="num">{{ row.studentId || '—' }}</td>
                <td>{{ describeUnmatchedRow(row) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="lastResult.unmatched.length > unmatchedRows.length" class="unmatched-more">
          未匹配记录较多，这里只列出前 {{ unmatchedRows.length }} 行。
        </p>
        <button
          class="btn btn-secondary result-export"
          type="button"
          data-testid="merge-export-unmatched"
          @click="exportUnmatched"
        >
          <Download :size="15" />
          导出为 CSV
        </button>
      </details>
      <p v-else class="result-empty">这份文件的每一行都匹配到了基准名单，没有需要人工处理的行。</p>
    </template>

    <template v-else>
      <div v-if="errorMessage" class="callout callout-danger merge-error">
        <AlertTriangle :size="16" />
        {{ errorMessage }}
      </div>

      <section class="sheet-section">
        <div class="section-head">
          <span class="section-no">1</span>
          <h3>成绩文件与范围</h3>
        </div>

        <FileDropzone
          v-if="!currentFileName"
          label="选择第二份 Excel"
          hint="至少包含姓名或学号列，以及要合并的数据列"
          test-id="score-file"
          @select="loadFile"
          @error="onFileError"
        />
        <template v-else>
          <div class="file-bar">
            <FileSpreadsheet :size="20" />
            <div>
              <strong>{{ currentFileName }}</strong>
              <span>{{ sheetNames.length }} 个工作表</span>
            </div>
          </div>

          <div v-if="isLoading" class="callout">
            <Loader2 class="spin" :size="16" />
            正在读取 Excel 文件，请稍候…
          </div>

          <template v-else>
            <div class="two-col" style="margin-bottom: 14px">
              <div v-if="sheetNames.length > 1">
                <label class="field-label" for="score-sheet-select">工作表</label>
                <select
                  id="score-sheet-select"
                  v-model="selectedSheet"
                  class="control"
                  data-testid="score-sheet-select"
                >
                  <option v-for="sheet in sheetNames" :key="sheet" :value="sheet">{{ sheet }}</option>
                </select>
                <p class="field-hint">成绩数据通常位于第一个工作表。</p>
              </div>
              <div v-else>
                <span class="field-label">工作表</span>
                <div class="file-bar" style="margin-bottom: 0">
                  <FileSpreadsheet :size="16" />
                  <div>
                    <strong>{{ sheetNames[0] || '未命名' }}</strong>
                    <span>单一工作表</span>
                  </div>
                </div>
              </div>
              <div>
                <span class="field-label">更换文件</span>
                <FileDropzone
                  compact
                  label="换一份成绩 Excel"
                  hint=".xlsx / .xls"
                  test-id="score-file-replace"
                  @select="loadFile"
                  @error="onFileError"
                />
              </div>
            </div>

            <div class="two-col">
              <div>
                <label class="field-label" for="score-skip-rows">跳过顶部行</label>
                <input
                  id="score-skip-rows"
                  v-model.number="skipRows"
                  class="control"
                  type="number"
                  min="0"
                  max="20"
                  step="1"
                  data-testid="score-skip-rows"
                />
                <p class="field-hint">跳过标题、说明等无用行。</p>
              </div>
              <div>
                <label class="field-label" for="score-skip-footer">跳过尾部行</label>
                <input
                  id="score-skip-footer"
                  v-model.number="skipFooter"
                  class="control"
                  type="number"
                  min="0"
                  max="50"
                  step="1"
                  data-testid="score-skip-footer"
                />
                <p class="field-hint">跳过汇总、统计等尾部行。</p>
              </div>
            </div>

            <div class="preview-block">
              <PreviewTable
                :columns="scoreTable.columns"
                :rows="scoreTable.rows"
                :limit="12"
                test-id="score-preview"
              />
            </div>
          </template>
        </template>
      </section>

      <template v-if="scoreColumns.length > 0">
        <section class="sheet-section">
          <div class="section-head">
            <span class="section-no">2</span>
            <h3>匹配列</h3>
          </div>
          <div class="match-row">
            <div class="match-select">
              <label class="field-label" for="match-col">用哪一列匹配学生？</label>
              <select
                id="match-col"
                v-model="matchCol"
                class="control"
                data-testid="match-col"
              >
                <option v-for="column in scoreColumns" :key="column.name" :value="column.name">
                  {{ column.name }}
                </option>
              </select>
              <p class="field-hint">{{ matchHint }}</p>
            </div>
            <span class="tag" :class="matchKind === 'unsupported' ? 'tag-seal' : 'tag-green'">
              {{ matchTag }}
            </span>
          </div>
          <div class="match-stats">
            <span class="tag" :class="matchSummaryClass" data-testid="match-summary">
              {{ matchSummaryText }}
            </span>
            <span v-if="currentMatchStat && currentMatchStat.matches === 0" class="match-note">
              基准名单中没有对应记录的行会被自动忽略
            </span>
          </div>
          <div v-if="suggestedMatch" class="callout callout-warn match-suggestion">
            <AlertTriangle :size="16" />
            <div>
              <p>当前匹配列与基准名单的匹配率较低，建议改用「{{ suggestedMatch.column }}」。</p>
              <button class="text-action" type="button" data-testid="use-suggested-match" @click="useSuggestedMatch">
                改用「{{ suggestedMatch.column }}」（可匹配 {{ suggestedMatch.matches }} / {{ suggestedMatch.total }} 行）
              </button>
            </div>
          </div>
        </section>

        <section class="sheet-section">
          <div class="section-head">
            <span class="section-no">3</span>
            <h3>要并入的数据列</h3>
          </div>
          <p class="section-desc">每个勾选的列都会作为独立列添加到基准名单。</p>
          <p v-if="dataOptions.length > 12" class="field-hint" style="margin: -0.35rem 0 0.65rem 2.75rem">
            该文件有 {{ dataOptions.length }} 个可选列，默认只选择主要成绩列；可按需勾选，或使用“全选数值列”。
          </p>

          <div v-if="dataOptions.length === 0" class="callout">
            <AlertTriangle :size="16" />
            这个文件除了匹配列之外没有其他列，请更换文件或调整跳过的行数。
          </div>
          <template v-else>
            <div class="chip-tools">
              <button
                class="text-action"
                type="button"
                :disabled="numericOptions.length === 0"
                @click="selectNumericColumns"
              >
                <Sparkles :size="13" />
                全选数值列
              </button>
              <button class="text-action" type="button" @click="clearColumns">清空</button>
              <span class="chip-count">已选 {{ selectedCols.length }} 列 / 可选 {{ dataOptions.length }} 列</span>
            </div>

            <div class="column-chips">
              <button
                v-for="(option, index) in dataOptions"
                :key="option.name"
                class="col-chip"
                :class="{ 'is-selected': selectedSet.has(option.name) }"
                type="button"
                :aria-pressed="selectedSet.has(option.name)"
                :data-testid="`data-col-${index}`"
                @click="toggleColumn(option.name)"
              >
                <span class="chip-check">
                  <Check v-if="selectedSet.has(option.name)" :size="12" :stroke-width="2.6" />
                </span>
                <span class="chip-name">{{ option.name }}</span>
                <span class="chip-kind">{{ option.kind === 'number' ? '数值' : '文本' }}</span>
              </button>
            </div>
          </template>
        </section>

        <section v-if="conflicts.length > 0" class="sheet-section">
          <div class="section-head">
            <span class="section-no">4</span>
            <h3>重名核对</h3>
          </div>
          <p class="section-desc">成绩表中出现同名学生，请为每一行选择对应的学生记录。</p>
          <div class="callout callout-warn">
            <AlertTriangle :size="16" />
            <div>
              发现 {{ conflicts.length }} 行成绩对应重名学生。{{ duplicateHint }}
            </div>
          </div>

          <div class="dup-list">
            <div v-for="group in conflictGroups" :key="group.name" class="dup-group">
              <div class="dup-group-head">
                <strong>{{ group.name }}</strong>
                <span class="tag tag-amber">{{ group.conflicts.length }} 行成绩</span>
                <span class="tag">{{ group.conflicts[0]?.candidateIndices.length }} 名同名学生</span>
              </div>
              <div v-for="conflict in group.conflicts" :key="conflict.key" class="dup-case">
                <div class="dup-case-head">
                  第 {{ conflict.scoreRowIndex + 1 }} 条成绩
                </div>
                <div class="dup-row">
                  <span v-for="column in conflictColumns" :key="column">
                    <em>{{ column }}</em>
                    {{ visibleValue(conflict.scoreRow, column) }}
                  </span>
                </div>
                <label class="dup-select">
                  <span>
                    对应学生
                    <span v-if="conflict.preferredIndex !== undefined" class="tag tag-green dup-auto-tag">
                      已按班级对应
                    </span>
                  </span>
                  <select
                    v-model.number="duplicateSelections[conflict.key]"
                    class="control"
                    :data-testid="`dup-select-${conflict.scoreRowIndex}`"
                  >
                    <option
                      v-for="candidate in conflict.candidateIndices"
                      :key="candidate"
                      :value="candidate"
                    >
                      {{ candidateLabel(candidate) }}
                    </option>
                  </select>
                </label>
              </div>
            </div>
          </div>
        </section>
      </template>
    </template>

    <template #footer>
      <span class="footer-note">
        <template v-if="lastResult">
          已写入当前名单
          <template v-if="unmatchedRows.length"> · {{ unmatchedRows.length }} 行未匹配</template>
        </template>
        <template v-else>
          已选 {{ selectedCols.length }} 列
          <template v-if="currentMatchStat"> · {{ matchSummaryText }}</template>
          <template v-if="conflicts.length > 0"> · {{ conflicts.length }} 个重名待核对</template>
        </template>
      </span>
      <div class="footer-actions">
        <template v-if="lastResult">
          <button
            class="btn btn-ghost"
            type="button"
            data-testid="merge-undo"
            title="把名单恢复到本次导入之前的状态"
            @click="undoImport"
          >
            撤销本次导入
          </button>
          <button
            class="btn btn-primary"
            type="button"
            data-testid="merge-done"
            @click="finish"
          >
            完成
          </button>
        </template>
        <template v-else>
          <button class="btn btn-ghost" type="button" @click="$emit('close')">取消</button>
          <button
            class="btn btn-primary"
            type="button"
            :disabled="!canImport"
            data-testid="merge-import"
            @click="doImport"
          >
            {{ selectedCols.length > 0 ? `导入 ${selectedCols.length} 列` : '导入数据列' }}
          </button>
        </template>
      </div>
    </template>
  </BaseSheet>
</template>

<style scoped>
.merge-error {
  margin-bottom: 1rem;
}

.merge-undo {
  margin-bottom: 1rem;
}

.merge-result {
  margin-bottom: 1.1rem;
  padding: 1.1rem 1.2rem;
  border: 1px solid #c3dbcc;
  border-radius: 14px;
  background: linear-gradient(180deg, #f3faf5, var(--surface));
}

.result-head {
  display: flex;
  gap: 0.7rem;
  align-items: flex-start;
}

.result-icon {
  flex: none;
  margin-top: 2px;
  color: #2f7d5b;
}

.result-head strong {
  display: block;
  font-size: 15.5px;
  font-weight: 600;
}

.result-head p {
  margin-top: 0.2rem;
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.6;
}

.result-meta {
  color: var(--muted) !important;
  font-size: 11px !important;
  opacity: 0.85;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
  gap: 0.55rem;
  margin-top: 1rem;
}

.result-stat {
  padding: 0.65rem 0.8rem;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
}

.result-stat span {
  color: var(--muted);
  font-size: 11px;
}

.result-stat strong {
  display: block;
  margin-top: 0.15rem;
  color: var(--ink);
  font-size: 26px;
  font-weight: 600;
  line-height: 1.15;
  font-variant-numeric: tabular-nums;
}

.result-stat em {
  margin-left: 0.18rem;
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
  font-weight: 500;
}

.result-stat.is-warn {
  border-color: var(--amber-line);
  background: var(--amber-bg);
}

.result-stat.is-warn strong {
  color: var(--amber);
}

.result-note {
  margin-top: 0.85rem;
  color: var(--muted);
  font-size: 11.5px;
  line-height: 1.6;
}

.result-block {
  margin-bottom: 1.1rem;
}

.result-block h4 {
  margin-bottom: 0.45rem;
  font-size: 12.5px;
  font-weight: 600;
}

.result-columns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.unmatched-block {
  margin-bottom: 1rem;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
}

.unmatched-block summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 0.9rem;
  cursor: pointer;
  font-size: 12.5px;
  font-weight: 600;
}

.unmatched-toggle {
  color: var(--muted);
  font-size: 11px;
  font-weight: 400;
}

.unmatched-lead {
  padding: 0 0.9rem;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.65;
}

.unmatched-table-wrap {
  max-height: 280px;
  margin: 0.6rem 0.9rem 0;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 10px;
}

.unmatched-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.unmatched-table th {
  position: sticky;
  top: 0;
  padding: 0.45rem 0.6rem;
  border-bottom: 1px solid var(--line);
  background: var(--surface-soft);
  color: var(--muted);
  font-weight: 600;
  text-align: left;
}

.unmatched-table td {
  padding: 0.45rem 0.6rem;
  border-bottom: 1px solid var(--line);
  color: var(--ink-soft);
}

.unmatched-table tr:last-child td {
  border-bottom: 0;
}

.unmatched-table .num {
  font-variant-numeric: tabular-nums;
}

.unmatched-more {
  padding: 0.4rem 0.9rem 0;
  color: var(--muted);
  font-size: 11.5px;
}

.result-export {
  margin: 0.7rem 0.9rem 0.9rem;
}

.result-empty {
  margin-bottom: 1rem;
  color: var(--muted);
  font-size: 12px;
}

.preview-block {
  margin-top: 0.85rem;
}

.match-row {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.match-select {
  flex: 1;
  max-width: 420px;
}

.match-row > .tag {
  margin-top: 1.72rem;
}

.match-stats {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem 0.7rem;
  margin-top: 0.65rem;
}

.match-note {
  color: var(--muted);
  font-size: 11.5px;
}

.match-suggestion {
  margin-top: 0.7rem;
}

.match-suggestion p {
  margin: 0;
  font-size: 12px;
}

.match-suggestion .text-action {
  margin-top: 0.3rem;
}

.chip-tools {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin-bottom: 0.6rem;
}

.text-action {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--pine-soft);
  font-size: 11.5px;
  font-weight: 500;
}

.text-action:hover:not(:disabled) {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.text-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.chip-count {
  margin-left: auto;
  color: var(--muted);
  font-size: 11.5px;
}

.column-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  max-height: 230px;
  overflow: auto;
  padding: 2px;
}

.col-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 32px;
  padding: 0.25rem 0.55rem 0.25rem 0.35rem;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: var(--ink-soft);
  font-size: 12px;
  transition:
    border-color 140ms ease,
    background-color 140ms ease,
    color 140ms ease;
}

.col-chip:hover {
  border-color: var(--pine-soft);
}

.col-chip.is-selected {
  border-color: #a8c8b9;
  background: var(--mint);
  color: #1e5341;
}

.chip-check {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 17px;
  height: 17px;
  border: 1px solid var(--line-strong);
  border-radius: 5px;
  background: var(--surface);
  color: var(--surface);
}

.col-chip.is-selected .chip-check {
  border-color: var(--pine-soft);
  background: var(--pine-soft);
  color: #fff;
}

.chip-name {
  font-weight: 500;
}

.chip-kind {
  color: var(--muted);
  font-size: 10px;
}

.col-chip.is-selected .chip-kind {
  color: #4e7c69;
}

.dup-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  max-height: 420px;
  margin-top: 0.7rem;
  overflow: auto;
  padding-right: 2px;
}

.dup-group {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
}

.dup-group-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--line);
  background: var(--surface-soft);
  border-radius: 10px 10px 0 0;
}

.dup-group-head strong {
  margin-right: 0.15rem;
  font-size: 13px;
}

.dup-case {
  padding: 0.65rem 0.75rem;
}

.dup-case + .dup-case {
  border-top: 1px dashed var(--line);
}

.dup-case-head {
  margin-bottom: 0.35rem;
  color: var(--muted);
  font-size: 11px;
}

.dup-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem 0.8rem;
  padding: 0.45rem 0.55rem;
  border-radius: 7px;
  background: var(--surface-soft);
  font-size: 11.5px;
}

.dup-row span {
  display: inline-flex;
  gap: 0.25rem;
  color: var(--ink-soft);
}

.dup-row em {
  color: var(--muted);
  font-style: normal;
}

.dup-select {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin-top: 0.5rem;
  font-size: 11.5px;
  color: var(--muted);
}

.dup-select span {
  flex: none;
}

.dup-auto-tag {
  margin-left: 0.25rem;
  transform: translateY(-1px);
}

.dup-select .control {
  max-width: 320px;
  height: 33px;
  font-size: 12px;
}

@media (max-width: 640px) {
  .result-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .result-stat strong {
    font-size: 22px;
  }
}
</style>
