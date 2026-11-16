<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { Download, ScanSearch, Users } from 'lucide-vue-next'
import { useSessionStore } from '../stores/session'
import DataTable from './DataTable.vue'
import FileDropzone from './FileDropzone.vue'
import ReportBanner from './ReportBanner.vue'
import SummaryStrip from './SummaryStrip.vue'

defineEmits<{
  'roster-file': [file: File]
  'open-merge': []
  copy: [focus: { sheet: string; className: string }]
  export: []
}>()

const session = useSessionStore()
const { hasData, studentCount, classCount, dataColumns, completeness, report } =
  storeToRefs(session)

const sampleRows = [
  { id: '2024001', name: '张三', className: '高一(1)班', mid: '84', final: '91' },
  { id: '2024002', name: '李四', className: '高一(1)班', mid: '76', final: '88' },
  { id: '2024003', name: '王五', className: '高一(2)班', mid: '92', final: '86' },
  { id: '2024004', name: '赵六', className: '高一(2)班', mid: '68', final: '74' },
  { id: '2024005', name: '孙七', className: '高一(3)班', mid: '88', final: '90' },
]
</script>

<template>
  <div class="workspace">
    <section v-if="!hasData" class="empty-state">
      <div class="empty-copy">
        <h1>把两份 Excel<br />合成一张干净的名单。</h1>
        <p class="empty-lead">
          基准名单决定顺序，第二份文件按姓名或学号并入。全程在浏览器里完成，不上传服务器。
        </p>
        <FileDropzone
          label="选择学生名单 Excel"
          hint="支持 .xlsx / .xls，先导入作为基准的名单"
          test-id="empty-roster-input"
          @select="$emit('roster-file', $event)"
        />
        <div class="empty-features">
          <span><ScanSearch :size="16" /> 自动识别姓名、学号、班级</span>
          <span><Users :size="16" /> 重名逐条核对</span>
          <span><Download :size="16" /> 合并后直接导出</span>
        </div>
        <p class="sample-links">
          没有文件？下载
          <a href="/samples/sample_roster.xlsx" download>示例名单</a>
          和
          <a href="/samples/sample_scores.xlsx" download>示例成绩表</a>
          试试。
        </p>
      </div>

      <aside class="sample-wrap" aria-hidden="true">
        <div class="sample-head">
          <span>合并后的名单</span>
          <span class="tag tag-green">按学号匹配</span>
        </div>
        <div class="sample-sheet">
          <div class="sample-row sample-header">
            <span>学号</span>
            <span>姓名</span>
            <span>班级</span>
            <span>期中</span>
            <span>期末</span>
          </div>
          <div v-for="row in sampleRows" :key="row.id" class="sample-row">
            <span>{{ row.id }}</span>
            <span class="sample-name">{{ row.name }}</span>
            <span>{{ row.className }}</span>
            <span class="sample-score">{{ row.mid }}</span>
            <span class="sample-score">{{ row.final }}</span>
          </div>
        </div>
        <p class="sample-foot">第二份文件顺序不同，也能按姓名或学号对上。</p>
      </aside>
    </section>

    <template v-else>
      <SummaryStrip
        :students="studentCount"
        :classes="classCount"
        :data-columns="dataColumns.length"
        :completeness="completeness"
      />
      <ReportBanner v-if="report" :report="report" @dismiss="session.dismissReport()" />
      <DataTable
        :columns="session.columns"
        :rows="session.rows"
        @open-merge="$emit('open-merge')"
        @copy="$emit('copy', $event)"
        @export="$emit('export')"
      />
    </template>
  </div>
</template>

<style scoped>
.workspace {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  min-width: 0;
}

.empty-state {
  display: grid;
  grid-template-columns: minmax(0, 1.22fr) minmax(330px, 0.78fr);
  align-items: center;
  gap: clamp(1.5rem, 3vw, 3rem);
  min-height: calc(100vh - 160px);
  padding: 1.5rem clamp(1rem, 3vw, 2.4rem) 2rem;
}

.empty-copy h1 {
  max-width: 13em;
  font-size: clamp(34px, 4.2vw, 50px);
  line-height: 1.22;
  letter-spacing: 0.005em;
}

.empty-lead {
  max-width: 48ch;
  margin: 1rem 0 1.4rem;
  color: var(--muted);
  font-size: 13.5px;
  line-height: 1.7;
}

.empty-copy :deep(.dropzone) {
  min-height: 128px;
}

.empty-features {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem 1.3rem;
  margin-top: 1.1rem;
  color: var(--ink-soft);
  font-size: 11.5px;
}

.empty-features span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.empty-features svg {
  color: var(--pine-soft);
}

.sample-links {
  margin-top: 0.9rem;
  color: var(--muted);
  font-size: 11px;
}

.sample-links a {
  font-weight: 500;
}

.sample-wrap {
  position: relative;
  transform: rotate(0.6deg);
}

.sample-wrap::before {
  content: '';
  position: absolute;
  inset: 14px -14px -14px 14px;
  z-index: -1;
  border: 1px solid rgba(13, 74, 61, 0.12);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.35);
}

.sample-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.55rem;
  padding: 0 0.2rem;
  color: var(--ink-soft);
  font-size: 11.5px;
  font-weight: 500;
}

.sample-sheet {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: 0 20px 50px rgba(16, 45, 35, 0.1);
}

.sample-row {
  display: grid;
  grid-template-columns: 1.15fr 0.8fr 1.2fr 0.62fr 0.62fr;
  gap: 0.5rem;
  padding: 0.6rem 0.85rem;
  border-bottom: 1px solid var(--line);
  color: var(--ink-soft);
  font-size: 11.5px;
  font-variant-numeric: tabular-nums;
}

.sample-row:last-child {
  border-bottom: 0;
}

.sample-row span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sample-header {
  background: #f2f6f2;
  color: var(--muted);
  font-size: 10.5px;
  font-weight: 600;
}

.sample-name {
  color: var(--ink);
  font-weight: 500;
}

.sample-score {
  text-align: right;
}

.sample-foot {
  margin-top: 0.65rem;
  padding: 0 0.2rem;
  color: var(--muted);
  font-size: 10.5px;
}

@media (max-width: 1120px) {
  .empty-state {
    grid-template-columns: 1fr;
    min-height: 0;
    gap: 2rem;
    padding-top: 0.6rem;
  }

  .sample-wrap {
    width: min(560px, 100%);
    transform: none;
  }

  .empty-copy h1 {
    max-width: 18ch;
  }
}

@media (max-width: 640px) {
  .empty-state {
    padding: 0.4rem 0.15rem 1.2rem;
  }

  .empty-copy h1 {
    font-size: 32px;
  }

  .empty-features {
    flex-direction: column;
    gap: 0.45rem;
  }

  .sample-row {
    padding: 0.5rem 0.6rem;
    font-size: 10.5px;
  }
}
</style>
