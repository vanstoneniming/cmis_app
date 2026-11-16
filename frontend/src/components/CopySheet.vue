<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { AlertTriangle, Check, ClipboardCopy, Layers, Sparkles } from 'lucide-vue-next'
import type { DataRow } from '../types'
import { displayCell, isEmptyCell } from '../lib/cells'
import { copyText } from '../lib/clipboard'
import { buildTsv, classesOf } from '../lib/sheets'
import { dataColumnsOf } from '../lib/transform'
import { useSessionStore } from '../stores/session'
import { useToastStore } from '../stores/toasts'
import BaseSheet from './BaseSheet.vue'

const props = defineProps<{ focus?: { sheet: string; className: string } | null }>()
defineEmits<{ close: [] }>()

const session = useSessionStore()
const toasts = useToastStore()

const groups = computed(() => session.sheetGroups)

/** 从数据表带过来的筛选条件：打开面板时定位到对应的表或班级 */
function initialIndex(): number {
  const list = groups.value
  const sheet = props.focus?.sheet
  if (sheet) {
    const found = list.findIndex((group) => group.name === sheet)
    if (found >= 0) return found
  }
  const className = props.focus?.className
  if (className) {
    const found = list.findIndex((group) =>
      group.indices.some(
        (index) => displayCell(session.rows[index]?.['班级'] ?? null).trim() === className,
      ),
    )
    if (found >= 0) return found
  }
  return 0
}

const activeIndex = ref(initialIndex())
const activeGroup = computed(() => groups.value[activeIndex.value] ?? groups.value[0] ?? null)

const columns = computed(() => session.columns)
const dataColumns = computed(() => dataColumnsOf(session.columns))

const selectedCols = ref<string[]>(dataColumns.value.slice())
const selectedSet = computed(() => new Set(selectedCols.value))

const activeRows = computed<DataRow[]>(() => {
  const group = activeGroup.value
  if (!group) return []
  return group.indices.map((index) => session.rows[index]!).filter(Boolean)
})

const sheetLabel = computed(() => activeGroup.value?.name || '未识别工作表')
const classLabel = computed(() => {
  const names = classesOf(activeRows.value)
  return names.length > 0 ? names.join('、') : '未识别班级'
})
const groupingLabel = computed(() => (session.hasSheetInfo ? '按工作表' : '按班级'))
const groupingNote = computed(() =>
  session.hasSheetInfo
    ? '按基础文件的工作表逐个复制，不会把所有班级合成一份。'
    : '这份名单导入时没有留下工作表信息（旧会话），已按班级拆分；重新导入基础名单后可按工作表拆分。',
)

const previewColumns = computed(() => selectedCols.value.slice(0, 8))
const previewRows = computed(() => activeRows.value.slice(0, 8))
const hiddenColumnCount = computed(() =>
  Math.max(0, selectedCols.value.length - previewColumns.value.length),
)

const rowCount = computed(() => activeRows.value.length)
const filledCount = computed(() => {
  const columns = selectedCols.value
  let filled = 0
  activeRows.value.forEach((row) => {
    columns.forEach((column) => {
      if (!isEmptyCell(row[column] ?? null)) filled += 1
    })
  })
  return filled
})
const canCopy = computed(() => selectedCols.value.length > 0 && rowCount.value > 0)

watch(groups, (list) => {
  if (activeIndex.value >= list.length) activeIndex.value = 0
})

function toggleColumn(name: string) {
  if (selectedSet.value.has(name)) {
    selectedCols.value = selectedCols.value.filter((column) => column !== name)
  } else {
    selectedCols.value = [...selectedCols.value, name]
  }
}

function selectDataColumns() {
  selectedCols.value = dataColumns.value.slice()
}

function selectAllColumns() {
  selectedCols.value = columns.value.slice()
}

function clearColumns() {
  selectedCols.value = []
}

function cellText(row: DataRow, column: string): string {
  return displayCell(row[column] ?? null) || '—'
}

async function copy() {
  if (!canCopy.value) return
  const ok = await copyText(buildTsv(selectedCols.value, activeRows.value))
  if (!ok) {
    toasts.error('复制失败', '浏览器没有授权剪贴板，请手动选中预览里的内容复制。')
    return
  }
  toasts.success(
    `已复制 ${rowCount.value} 行 × ${selectedCols.value.length} 列`,
    `「${sheetLabel.value}」的学生顺序与原表一致，回到 Excel 从第一名学生的单元格开始粘贴即可。`,
  )
}

async function copyColumn(column: string) {
  const ok = await copyText(buildTsv([column], activeRows.value))
  if (!ok) {
    toasts.error('复制失败', '浏览器没有授权剪贴板，请手动复制。')
    return
  }
  toasts.success(
    `已复制「${column}」${rowCount.value} 行`,
    `粘贴到原表该列第一名学生的单元格即可。`,
  )
}
</script>

<template>
  <BaseSheet
    title="按工作表复制数据"
    subtitle="工具只处理数据、不改动原始文件：按原表学生顺序复制，由你粘回 Excel 对应位置。"
    test-id="copy-sheet"
    @close="$emit('close')"
  >
    <div v-if="groups.length === 0" class="callout callout-warn">
      <AlertTriangle :size="16" />
      当前会话没有可复制的数据。
    </div>

    <template v-else>
      <section class="sheet-section">
        <div class="section-head">
          <span class="section-no">1</span>
          <h3>工作表（班级）</h3>
        </div>
        <p class="section-desc">
          {{ groupingNote }}一次只复制一个{{ groupingLabel === '按工作表' ? '工作表' : '班级' }}，行顺序与导入时一致；粘贴前请确认原表学生块中间没有空行。
        </p>
        <div class="sheet-chips">
          <button
            v-for="(group, index) in groups"
            :key="`${group.name}-${index}`"
            type="button"
            class="sheet-chip"
            :class="{ 'is-active': index === activeIndex }"
            :title="classesOf(group.indices.map((rowIndex) => session.rows[rowIndex]!)).join('、')"
            :data-testid="`copy-sheet-${index}`"
            @click="activeIndex = index"
          >
            <Layers :size="14" />
            <span class="sheet-chip-name">{{ group.name || '未识别工作表' }}</span>
            <span class="sheet-chip-count">{{ group.indices.length }} 人</span>
          </button>
        </div>
        <p class="field-hint">
          当前：{{ sheetLabel }} · {{ classLabel }} · {{ rowCount }} 名学生
          <template v-if="session.hasSheetInfo && activeGroup?.name">
            （原表工作表「{{ activeGroup.name }}」）
          </template>
        </p>
      </section>

      <section class="sheet-section">
        <div class="section-head">
          <span class="section-no">2</span>
          <h3>要复制的列</h3>
        </div>
        <p class="section-desc">
          复制成制表符分隔的表格，粘进 Excel 会按列自动对齐；空单元格会留空占位，保证行对得上。
        </p>
        <div class="chip-tools">
          <button class="text-action" type="button" @click="selectDataColumns">
            <Sparkles :size="13" />
            全选数据列
          </button>
          <button class="text-action" type="button" @click="selectAllColumns">全选所有列</button>
          <button class="text-action" type="button" @click="clearColumns">清空</button>
          <span class="chip-count">已选 {{ selectedCols.length }} 列 / 共 {{ columns.length }} 列</span>
        </div>
        <div class="column-chips">
          <button
            v-for="(column, index) in columns"
            :key="column"
            type="button"
            class="col-chip"
            :class="{ 'is-selected': selectedSet.has(column) }"
            :aria-pressed="selectedSet.has(column)"
            :data-testid="`copy-col-${index}`"
            @click="toggleColumn(column)"
          >
            <span class="chip-check">
              <Check v-if="selectedSet.has(column)" :size="12" :stroke-width="2.6" />
            </span>
            <span class="chip-name">{{ column }}</span>
            <span class="chip-kind">{{ dataColumns.includes(column) ? '数据' : '名单' }}</span>
          </button>
        </div>
      </section>

      <section class="sheet-section">
        <div class="section-head">
          <span class="section-no">3</span>
          <h3>预览</h3>
        </div>
        <p v-if="selectedCols.length === 0" class="callout">
          还没有选择要复制的列。
        </p>
        <template v-else>
          <div class="preview-wrap">
            <table class="copy-preview">
              <thead>
                <tr>
                  <th scope="col" class="row-no">#</th>
                  <th v-for="column in previewColumns" :key="column" scope="col">
                    <span class="preview-head">
                      {{ column }}
                      <button
                        class="preview-copy"
                        type="button"
                        :title="`复制「${column}」整列`"
                        :aria-label="`复制「${column}」整列`"
                        :data-testid="`copy-col-only-${column}`"
                        @click="copyColumn(column)"
                      >
                        <ClipboardCopy :size="12" />
                      </button>
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, rowIndex) in previewRows" :key="rowIndex">
                  <td class="row-no">{{ rowIndex + 1 }}</td>
                  <td v-for="column in previewColumns" :key="column">
                    {{ cellText(row, column) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="preview-note">
            预览显示前 {{ previewRows.length }} 行 × {{ previewColumns.length }} 列<template
              v-if="hiddenColumnCount > 0"
            >，还有 {{ hiddenColumnCount }} 列未展示</template>；实际复制 {{ rowCount }} 行全部数据。
          </p>
        </template>
      </section>
    </template>

    <template #footer>
      <span class="footer-note">
        已选 {{ selectedCols.length }} 列 · {{ rowCount }} 行 · 非空单元格 {{ filledCount }} 个
      </span>
      <div class="footer-actions">
        <button class="btn btn-ghost" type="button" @click="$emit('close')">关闭</button>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="!canCopy"
          data-testid="copy-run"
          @click="copy"
        >
          <ClipboardCopy :size="15" />
          复制到剪贴板
        </button>
      </div>
    </template>
  </BaseSheet>
</template>

<style scoped>
.sheet-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  max-height: 168px;
  overflow: auto;
  padding: 2px;
}

.sheet-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 34px;
  padding: 0.25rem 0.6rem;
  border: 1px solid var(--line);
  border-radius: 9px;
  background: var(--surface);
  color: var(--ink-soft);
  font-size: 12px;
}

.sheet-chip:hover {
  border-color: var(--pine-soft);
}

.sheet-chip.is-active {
  border-color: #a8c8b9;
  background: var(--mint);
  color: #1e5341;
}

.sheet-chip-name {
  font-weight: 500;
}

.sheet-chip-count {
  color: var(--muted);
  font-size: 10.5px;
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

.text-action:hover {
  text-decoration: underline;
  text-underline-offset: 3px;
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
  max-height: 200px;
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

.preview-wrap {
  max-height: 260px;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 10px;
}

.copy-preview {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.copy-preview th,
.copy-preview td {
  padding: 0.4rem 0.6rem;
  border-bottom: 1px solid var(--line);
  border-right: 1px solid var(--line);
  text-align: left;
  white-space: nowrap;
}

.copy-preview th {
  position: sticky;
  top: 0;
  background: var(--surface-soft);
  color: var(--muted);
  font-weight: 600;
}

.copy-preview tr:last-child td {
  border-bottom: 0;
}

.copy-preview .row-no {
  width: 44px;
  color: var(--muted);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.preview-head {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.preview-copy {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: var(--surface);
  color: var(--pine-soft);
}

.preview-copy:hover {
  border-color: var(--pine-soft);
  background: var(--mint);
}

.preview-note {
  margin-top: 0.5rem;
  color: var(--muted);
  font-size: 11.5px;
}
</style>
