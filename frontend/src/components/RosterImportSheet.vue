<script setup lang="ts">
import { computed, ref, shallowRef, watch } from 'vue'
import type { WorkBook } from 'xlsx'
import { AlertTriangle, FileSpreadsheet, Loader2, Sparkles } from 'lucide-vue-next'
import type { DataRow, TableData } from '../types'
import { displayCell } from '../lib/cells'
import { getSheetNames, readGrid, readWorkbook } from '../lib/excel'
import { buildStudentsFromTable, gridToTable, prepareRosterTable } from '../lib/transform'
import { useSessionStore } from '../stores/session'
import BaseSheet from './BaseSheet.vue'
import FileDropzone from './FileDropzone.vue'
import PreviewTable from './PreviewTable.vue'

const props = defineProps<{ file: File | null }>()

const emit = defineEmits<{
  close: []
  loaded: [payload: { count: number; classes: number; warnings: string[] }]
}>()

const session = useSessionStore()

const workbook = shallowRef<WorkBook | null>(null)
const sheetNames = ref<string[]>([])
const currentFileName = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const sheetMode = ref<'all' | 'single'>('all')
const selectedSheet = ref('')
const skipRows = ref(0)
const skipFooter = ref(0)
const nameCol = ref('')
const idCol = ref('')
const classCol = ref('')
const mappingTouched = ref(false)
const replacePending = ref(false)

const previewSheetName = computed(() =>
  sheetMode.value === 'all' ? (sheetNames.value[0] ?? '') : selectedSheet.value,
)

const previewRawTable = computed<TableData>(() => {
  if (!workbook.value || !previewSheetName.value) return { columns: [], rows: [] }
  return gridToTable(
    readGrid(workbook.value, previewSheetName.value),
    Math.max(0, Number(skipRows.value) || 0),
    Math.max(0, Number(skipFooter.value) || 0),
  )
})

const detection = computed(() => prepareRosterTable(previewRawTable.value))
const previewColumns = computed(() => detection.value.table.columns)
const previewRows = computed(() => detection.value.table.rows)
const sheetsToLoad = computed(() =>
  sheetMode.value === 'all' ? sheetNames.value : [selectedSheet.value].filter(Boolean),
)
const sampleNote = computed(() => {
  const names = sheetsToLoad.value
  if (names.length === 0) return '尚未选择工作表'
  return names.length === 1 ? `将读取工作表：${names[0]}` : `将读取 ${names.length} 个工作表，并按工作表名补充班级`
})

const mappedPreview = computed(() => {
  const columns = previewColumns.value
  const name = nameCol.value
  if (columns.length === 0 || !name || !columns.includes(name)) {
    return { rows: [] as DataRow[], error: '' }
  }
  try {
    const fallbackClass =
      sheetMode.value === 'all' && sheetsToLoad.value.length > 1 ? previewSheetName.value : ''
    const built = buildStudentsFromTable(
      detection.value.table,
      {
        nameCol: name,
        idCol: idCol.value && columns.includes(idCol.value) ? idCol.value : detection.value.mapping.idCol,
        classCol:
          classCol.value && columns.includes(classCol.value)
            ? classCol.value
            : detection.value.mapping.classCol,
      },
      { fallbackClass },
    )
    return { rows: built.rows, error: '' }
  } catch (error) {
    return {
      rows: [] as DataRow[],
      error: error instanceof Error ? error.message : '无法预览识别结果',
    }
  }
})

watch(
  () => props.file,
  (file) => {
    if (file) void loadFile(file)
  },
  { immediate: true },
)

watch(previewColumns, (columns) => {
  if (columns.length === 0) {
    nameCol.value = ''
    return
  }
  if (!nameCol.value || !columns.includes(nameCol.value)) {
    nameCol.value = detection.value.mapping.nameCol || columns[0] || ''
  }
  if (!mappingTouched.value) {
    idCol.value = detection.value.mapping.idCol
    classCol.value = detection.value.mapping.classCol
  } else {
    if (idCol.value && !columns.includes(idCol.value)) idCol.value = detection.value.mapping.idCol
    if (classCol.value && !columns.includes(classCol.value)) {
      classCol.value = detection.value.mapping.classCol
    }
  }
})

watch([skipRows, skipFooter, sheetMode, selectedSheet], () => {
  mappingTouched.value = false
  const columns = detection.value.table.columns
  nameCol.value = detection.value.mapping.nameCol || columns[0] || ''
  idCol.value = detection.value.mapping.idCol
  classCol.value = detection.value.mapping.classCol
})

async function loadFile(file: File) {
  isLoading.value = true
  errorMessage.value = ''
  replacePending.value = false
  workbook.value = null
  sheetNames.value = []
  try {
    const parsed = await readWorkbook(file)
    workbook.value = parsed
    sheetNames.value = getSheetNames(parsed)
    selectedSheet.value = sheetNames.value[0] ?? ''
    sheetMode.value = sheetNames.value.length > 1 ? 'all' : 'single'
    currentFileName.value = file.name
    skipRows.value = 0
    skipFooter.value = 0
    mappingTouched.value = false
    nameCol.value = ''
    idCol.value = ''
    classCol.value = ''
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

function submit() {
  if (!workbook.value) return
  if (session.hasData && !replacePending.value) {
    replacePending.value = true
    return
  }
  errorMessage.value = ''
  try {
    const sheets = sheetsToLoad.value
    if (sheets.length === 0) throw new Error('请选择要导入的工作表')

    const allRows: DataRow[] = []
    const warnings: string[] = []
    let nextIndex = 1
    const useSheetClass = sheets.length > 1

    for (const sheetName of sheets) {
      const rawTable = gridToTable(
        readGrid(workbook.value, sheetName),
        Math.max(0, Number(skipRows.value) || 0),
        Math.max(0, Number(skipFooter.value) || 0),
      )
      const sheetDetection = prepareRosterTable(rawTable)
      const columns = sheetDetection.table.columns
      if (columns.length === 0) continue

      const resolvedName =
        nameCol.value && columns.includes(nameCol.value)
          ? nameCol.value
          : sheetDetection.mapping.nameCol || columns[0] || ''
      if (!resolvedName) {
        throw new Error(`工作表「${sheetName}」中无法识别姓名列，请返回列映射手动选择`)
      }
      const resolvedId =
        idCol.value && columns.includes(idCol.value) ? idCol.value : sheetDetection.mapping.idCol
      const resolvedClass =
        classCol.value && columns.includes(classCol.value)
          ? classCol.value
          : sheetDetection.mapping.classCol

      const built = buildStudentsFromTable(
        sheetDetection.table,
        { nameCol: resolvedName, idCol: resolvedId, classCol: resolvedClass },
        {
          fallbackClass: useSheetClass && !resolvedClass ? sheetName : '',
          startIndex: nextIndex,
        },
      )
      allRows.push(...built.rows)
      warnings.push(...built.warnings)
      nextIndex = built.nextIndex
    }

    if (allRows.length === 0) {
      throw new Error('没有读到有效学生，请检查跳过的行数或姓名列设置')
    }

    session.setRoster(allRows, { fileName: currentFileName.value || '学生名单.xlsx' })
    const classes = new Set(
      allRows.map((row) => displayCell(row['班级'] ?? null)).filter(Boolean),
    ).size
    emit('loaded', { count: allRows.length, classes, warnings: [...new Set(warnings)] })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载学生名单失败'
  }
}
</script>

<template>
  <BaseSheet
    title="导入学生名单"
    subtitle="第一份 Excel 决定名单顺序，也是后续合并的基准。"
    test-id="roster-sheet"
    @close="$emit('close')"
  >
    <div
      v-if="replacePending"
      class="callout callout-warn replace-warning"
      role="alert"
      data-testid="roster-replace-warning"
    >
      <AlertTriangle :size="17" />
      <div>
        <strong>当前会话已有 {{ session.studentCount }} 名学生</strong>
        <p>继续加载会替换现有名单，并清除已经合并的数据列。</p>
      </div>
    </div>

    <section class="sheet-section">
      <div class="section-head">
        <span class="section-no">1</span>
        <h3>文件与范围</h3>
      </div>

      <FileDropzone
        v-if="!currentFileName"
        label="选择学生名单 Excel"
        hint="支持 .xlsx / .xls，文件应包含姓名列"
        test-id="roster-file"
        @select="loadFile"
        @error="onFileError"
      />
      <template v-else>
        <div class="file-bar">
          <FileSpreadsheet :size="20" />
          <div>
            <strong>{{ currentFileName }}</strong>
            <span>
              {{ sheetNames.length }} 个工作表
              <template v-if="isLoading"> · 正在读取…</template>
            </span>
          </div>
        </div>

        <div v-if="isLoading" class="callout">
          <Loader2 class="spin" :size="16" />
          正在读取 Excel 文件，请稍候…
        </div>

        <template v-else>
          <div v-if="sheetNames.length > 1" class="two-col" style="margin-bottom: 14px">
            <div>
              <span class="field-label">工作表导入方式</span>
              <div class="segmented" role="group" aria-label="工作表导入方式">
                <button
                  type="button"
                  :class="{ 'is-active': sheetMode === 'all' }"
                  data-testid="roster-sheet-mode-all"
                  @click="sheetMode = 'all'"
                >
                  导入全部工作表
                </button>
                <button
                  type="button"
                  :class="{ 'is-active': sheetMode === 'single' }"
                  data-testid="roster-sheet-mode-single"
                  @click="sheetMode = 'single'"
                >
                  选择单个工作表
                </button>
              </div>
              <p class="field-hint">{{ sampleNote }}</p>
            </div>
            <div>
              <label class="field-label" for="roster-sheet-select">工作表</label>
              <select
                id="roster-sheet-select"
                v-model="selectedSheet"
                class="control"
                :disabled="sheetMode === 'all'"
                data-testid="roster-sheet-select"
              >
                <option v-for="sheet in sheetNames" :key="sheet" :value="sheet">{{ sheet }}</option>
              </select>
              <p class="field-hint">全部导入时，每个工作表会作为一个班级来源。</p>
            </div>
          </div>
          <div v-else class="callout" style="margin-bottom: 14px">
            <FileSpreadsheet :size="16" />
            检测到 1 个工作表：{{ sheetNames[0] || '未命名' }}
          </div>

          <div class="two-col">
            <div>
              <label class="field-label" for="roster-skip-rows">跳过顶部行</label>
              <input
                id="roster-skip-rows"
                v-model.number="skipRows"
                class="control"
                type="number"
                min="0"
                max="20"
                step="1"
                data-testid="roster-skip-rows"
              />
              <p class="field-hint">用于去掉标题、说明等无用行。</p>
            </div>
            <div>
              <label class="field-label" for="roster-skip-footer">跳过尾部行</label>
              <input
                id="roster-skip-footer"
                v-model.number="skipFooter"
                class="control"
                type="number"
                min="0"
                max="50"
                step="1"
                data-testid="roster-skip-footer"
              />
              <p class="field-hint">用于去掉汇总、备注等尾部行。</p>
            </div>
          </div>

          <div class="preview-block">
            <PreviewTable
              :columns="previewColumns"
              :rows="previewRows"
              :limit="10"
              test-id="roster-preview"
            />
          </div>
        </template>
      </template>

      <div v-if="errorMessage" class="callout callout-danger" style="margin-top: 0.8rem">
        <AlertTriangle :size="16" />
        {{ errorMessage }}
      </div>
    </section>

    <section class="sheet-section">
      <div class="section-head">
        <span class="section-no">2</span>
        <h3>列映射</h3>
      </div>
      <p class="section-desc">系统会自动识别姓名、学号和班级列，也可以手动调整。</p>

      <div v-if="previewColumns.length === 0" class="callout">
        <AlertTriangle :size="16" />
        当前范围没有可用的列，请调整跳过行数或更换工作表。
      </div>
      <template v-else>
        <div v-if="detection.split" class="callout callout-success">
          <Sparkles :size="16" />
          检测到「{{ detection.split.sourceCol }}」包含“姓名 (学号)”格式，已自动拆分为「{{
            detection.split.nameCol
          }}」和「{{ detection.split.idCol }}」。
        </div>

        <div class="three-col" style="margin-top: 0.7rem">
          <div>
            <label class="field-label" for="roster-name-col">姓名列 *</label>
            <select
              id="roster-name-col"
              v-model="nameCol"
              class="control"
              data-testid="roster-name-col"
              @change="mappingTouched = true"
            >
              <option v-for="column in previewColumns" :key="column" :value="column">
                {{ column }}
              </option>
            </select>
          </div>
          <div>
            <label class="field-label" for="roster-id-col">学号列（可选）</label>
            <select
              id="roster-id-col"
              v-model="idCol"
              class="control"
              data-testid="roster-id-col"
              @change="mappingTouched = true"
            >
              <option value="">自动识别</option>
              <option v-for="column in previewColumns" :key="column" :value="column">
                {{ column }}
              </option>
            </select>
            <p class="field-hint">没有学号时会自动生成唯一标识。</p>
          </div>
          <div>
            <label class="field-label" for="roster-class-col">班级列（可选）</label>
            <select
              id="roster-class-col"
              v-model="classCol"
              class="control"
              data-testid="roster-class-col"
              @change="mappingTouched = true"
            >
              <option value="">自动识别</option>
              <option v-for="column in previewColumns" :key="column" :value="column">
                {{ column }}
              </option>
            </select>
            <p class="field-hint">没有班级列时，多工作表导入会用表名补充。</p>
          </div>
        </div>

        <div class="mapped-preview">
          <div class="mapped-preview-head">
            <strong>识别结果预览</strong>
            <span v-if="mappedPreview.rows.length">已识别 {{ mappedPreview.rows.length }} 名学生</span>
          </div>
          <div v-if="mappedPreview.error" class="callout callout-danger">
            <AlertTriangle :size="16" />
            {{ mappedPreview.error }}
          </div>
          <PreviewTable
            v-else
            :columns="['学号', '姓名', '班级']"
            :rows="mappedPreview.rows"
            :limit="8"
            caption="正式导入时会对每个工作表重复这一过程，并读取全部行"
            test-id="roster-mapped-preview"
          />
        </div>
      </template>
    </section>

    <template #footer>
      <span class="footer-note" :class="{ 'footer-warn': replacePending }">
        <template v-if="replacePending">
          确认后将替换当前名单并清除已合并的数据列
        </template>
        <template v-else>
          {{ previewRows.length }} 行预览 · {{ sheetsToLoad.length }} 个工作表待读取
        </template>
      </span>
      <div class="footer-actions">
        <template v-if="replacePending">
          <button class="btn btn-secondary" type="button" @click="replacePending = false">取消替换</button>
          <button
            class="btn btn-danger"
            type="button"
            data-testid="roster-replace-confirm"
            @click="submit"
          >
            确认替换
          </button>
        </template>
        <template v-else>
          <button class="btn btn-ghost" type="button" @click="$emit('close')">取消</button>
          <button
            class="btn btn-primary"
            type="button"
            :disabled="!workbook || isLoading || previewColumns.length === 0"
            data-testid="roster-load"
            @click="submit"
          >
            加载学生名单
          </button>
        </template>
      </div>
    </template>
  </BaseSheet>
</template>

<style scoped>
.preview-block {
  margin-top: 0.85rem;
}

.mapped-preview {
  margin-top: 1rem;
  padding-top: 0.9rem;
  border-top: 1px dashed var(--line);
}

.mapped-preview-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.45rem;
}

.mapped-preview-head strong {
  font-size: 12.5px;
  font-weight: 600;
}

.mapped-preview-head span {
  color: var(--muted);
  font-size: 11px;
}

.replace-warning {
  margin-bottom: 1rem;
}

.replace-warning strong {
  display: block;
  font-size: 12.5px;
  font-weight: 600;
}

.replace-warning p {
  margin-top: 0.15rem;
  font-size: 12px;
}

.footer-warn {
  color: var(--amber);
  font-weight: 500;
}
</style>
