<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import type { MergeReport } from './types'
import { exportTable, timestampSuffix } from './lib/excel'
import { useSessionStore } from './stores/session'
import { useToastStore } from './stores/toasts'
import AppHeader from './components/AppHeader.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import DataWorkspace from './components/DataWorkspace.vue'
import MergeSheet from './components/MergeSheet.vue'
import RosterImportSheet from './components/RosterImportSheet.vue'
import ToastStack from './components/ToastStack.vue'
import WorkflowRail from './components/WorkflowRail.vue'

const session = useSessionStore()
const toasts = useToastStore()
const { hasData, studentCount, dataColumns, rosterFileName } = storeToRefs(session)

const rosterFile = ref<File | null>(null)
const rosterOpen = ref(false)
const mergeOpen = ref(false)
const clearPending = ref(false)
let persistTimer: number | undefined

session.hydrate()

watch(
  () => [session.columns, session.rows, session.report, session.rosterFileName],
  () => {
    if (persistTimer) window.clearTimeout(persistTimer)
    persistTimer = window.setTimeout(() => session.persist(), 350)
  },
  { deep: true },
)

function openRoster(file: File) {
  rosterFile.value = file
  rosterOpen.value = true
}

function closeRoster() {
  rosterOpen.value = false
  rosterFile.value = null
}

function onRosterLoaded(payload: { count: number; classes: number; warnings: string[] }) {
  rosterOpen.value = false
  rosterFile.value = null
  toasts.success(
    `已加载 ${payload.count} 名学生`,
    payload.classes > 0 ? `${payload.classes} 个班级已识别` : '可以继续导入成绩数据列',
  )
  payload.warnings.slice(0, 2).forEach((warning) => {
    toasts.info('名单提示', warning)
  })
}

function openMerge() {
  if (!hasData.value) {
    toasts.info('先导入学生名单', '完成第 1 步后即可合并成绩数据。')
    return
  }
  mergeOpen.value = true
}

function onMergeImported(report: MergeReport) {
  const ignored = report.unmatched.length
  toasts.success(
    report.title,
    ignored > 0
      ? `已忽略 ${ignored} 行基准名单中没有的记录。`
      : `${report.addedColumns.length} 个数据列已加入名单。`,
  )
}

async function exportExcel() {
  if (!hasData.value) return
  try {
    await exportTable(
      { columns: session.columns, rows: session.rows },
      `数据统计_${timestampSuffix()}.xlsx`,
    )
    toasts.success('Excel 已导出', `共 ${session.rows.length} 名学生`)
  } catch (error) {
    toasts.error(
      '导出失败',
      error instanceof Error ? error.message : '请稍后重试',
    )
  }
}

function requestClear() {
  if (!hasData.value) return
  clearPending.value = true
}

function confirmClear() {
  session.clear()
  rosterOpen.value = false
  rosterFile.value = null
  mergeOpen.value = false
  clearPending.value = false
  toasts.info('已清空当前会话', '可以重新导入一份名单。')
}

function flushPersist() {
  if (persistTimer) window.clearTimeout(persistTimer)
  session.persist()
}

onMounted(() => {
  window.addEventListener('beforeunload', flushPersist)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', flushPersist)
  if (persistTimer) window.clearTimeout(persistTimer)
})
</script>

<template>
  <div class="app-shell">
    <AppHeader
      :has-data="hasData"
      :student-count="studentCount"
      :roster-file-name="rosterFileName"
      @export="exportExcel"
      @clear="requestClear"
    />

    <main class="app-body">
      <div class="rail-column">
        <WorkflowRail
          :has-data="hasData"
          :student-count="studentCount"
          :roster-file-name="rosterFileName"
          :data-column-count="dataColumns.length"
          @roster-file="openRoster"
          @open-merge="openMerge"
          @export="exportExcel"
          @clear="requestClear"
        />
      </div>
      <div class="workspace-column">
        <DataWorkspace
          @roster-file="openRoster"
          @open-merge="openMerge"
          @export="exportExcel"
        />
      </div>
    </main>

    <RosterImportSheet
      v-if="rosterOpen"
      :file="rosterFile"
      @close="closeRoster"
      @loaded="onRosterLoaded"
    />
    <MergeSheet v-if="mergeOpen" @close="mergeOpen = false" @imported="onMergeImported" />
    <ConfirmDialog
      v-if="clearPending"
      title="清空当前会话？"
      :message="`将移除 ${studentCount} 名学生和已经合并的数据列，此操作不可撤销。`"
      confirm-label="清空数据"
      cancel-label="保留数据"
      tone="danger"
      @confirm="confirmClear"
      @cancel="clearPending = false"
    />
    <ToastStack />
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-body {
  display: grid;
  grid-template-columns: 330px minmax(0, 1fr);
  gap: 1.35rem;
  align-items: start;
  width: min(1480px, 100%);
  margin: 0 auto;
  padding: 1.35rem 1.75rem 2.5rem;
  flex: 1;
}

.rail-column {
  position: sticky;
  top: 88px;
  min-width: 0;
}

.workspace-column {
  min-width: 0;
}

@media (max-width: 1080px) {
  .app-body {
    grid-template-columns: 292px minmax(0, 1fr);
    gap: 1rem;
    padding: 1.1rem 1rem 2rem;
  }
}

@media (max-width: 980px) {
  .app-body {
    grid-template-columns: 1fr;
  }

  .rail-column {
    position: static;
  }
}

@media (max-width: 640px) {
  .app-body {
    padding: 0.8rem 0.65rem 1.5rem;
  }
}
</style>
