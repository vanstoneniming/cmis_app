<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle2, Download, X } from 'lucide-vue-next'
import type { MergeReport } from '../types'
import { downloadCsv } from '../lib/csv'
import { timestampSuffix } from '../lib/excel'
import { describeUnmatchedRow } from '../lib/transform'

const props = defineProps<{ report: MergeReport }>()
defineEmits<{ dismiss: [] }>()

/** 旧会话里的报告只有 unmatched 字符串，没有结构化明细 */
const rows = computed(() => props.report.unmatchedRows ?? [])
const visibleUnmatched = computed(() => props.report.unmatched.slice(0, 10))
const hiddenUnmatched = computed(() => Math.max(0, props.report.unmatched.length - 10))
const unmatchedCount = computed(() => Math.max(props.report.unmatched.length, rows.value.length))

function exportUnmatched() {
  if (!rows.value.length) return
  downloadCsv(
    `未匹配学生_${timestampSuffix()}.csv`,
    ['行号', '姓名', '班级', '学号', '未匹配原因'],
    rows.value.map((row) => [
      String(row.rowNumber),
      row.name || '—',
      row.className || '—',
      row.studentId || '—',
      describeUnmatchedRow(row),
    ]),
  )
}
</script>

<template>
  <section class="report report-ok" data-testid="merge-report">
    <span class="report-icon">
      <CheckCircle2 :size="19" />
    </span>
    <div class="report-body">
      <div class="report-head">
        <strong>{{ report.title }}</strong>
        <button class="report-close" type="button" aria-label="关闭合并报告" @click="$emit('dismiss')">
          <X :size="15" />
        </button>
      </div>
      <ul class="report-details">
        <li v-for="detail in report.details" :key="detail">{{ detail }}</li>
      </ul>
      <div v-if="report.addedColumns.length" class="report-columns">
        <span class="report-columns-label">新增列</span>
        <span v-for="column in report.addedColumns" :key="column" class="tag tag-green">
          {{ column }}
        </span>
      </div>
      <div v-if="report.renamedColumns.length" class="report-columns">
        <span class="report-columns-label">重名已调整</span>
        <span v-for="item in report.renamedColumns" :key="item.to" class="tag">
          {{ item.from }} → {{ item.to }}
        </span>
      </div>

      <details v-if="unmatchedCount" class="report-unmatched">
        <summary>查看未匹配的 {{ unmatchedCount }} 行</summary>
        <template v-if="rows.length">
          <div class="report-table-wrap">
            <table class="report-table">
              <thead>
                <tr>
                  <th scope="col">行号</th>
                  <th scope="col">姓名</th>
                  <th scope="col">班级</th>
                  <th scope="col">学号</th>
                  <th scope="col">原因</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in rows" :key="`${row.rowNumber}-${row.matchedValue}`">
                  <td class="num">{{ row.rowNumber }}</td>
                  <td>{{ row.name || '—' }}</td>
                  <td>{{ row.className || '—' }}</td>
                  <td class="num">{{ row.studentId || '—' }}</td>
                  <td>{{ describeUnmatchedRow(row) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <button class="report-export" type="button" @click="exportUnmatched">
            <Download :size="13" />
            导出为 CSV
          </button>
        </template>
        <template v-else>
          <ul>
            <li v-for="line in visibleUnmatched" :key="line">{{ line }}</li>
          </ul>
          <p v-if="hiddenUnmatched > 0">还有 {{ hiddenUnmatched }} 行未列出。</p>
        </template>
      </details>
    </div>
  </section>
</template>

<style scoped>
.report {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.9rem;
  padding: 0.9rem 1rem;
  border: 1px solid #c3dbcc;
  border-radius: 12px;
  background: var(--mint);
  color: #234f3f;
}

.report-icon {
  flex: none;
  margin-top: 1px;
}

.report-body {
  min-width: 0;
  flex: 1;
}

.report-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.report-head strong {
  font-size: 13.5px;
  font-weight: 600;
}

.report-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin: -0.25rem -0.2rem 0 0;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: inherit;
  opacity: 0.65;
}

.report-close:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.05);
}

.report-details {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 1rem;
  margin: 0.25rem 0 0;
  padding: 0;
  list-style: none;
  font-size: 12px;
}

.report-details li {
  position: relative;
  padding-left: 0.7rem;
}

.report-details li::before {
  content: '';
  position: absolute;
  top: 0.55em;
  left: 0;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.55;
}

.report-columns {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.5rem;
}

.report-columns-label {
  margin-right: 0.1rem;
  font-size: 11.5px;
  opacity: 0.8;
}

.report-unmatched {
  margin-top: 0.55rem;
  font-size: 12px;
}

.report-unmatched summary {
  cursor: pointer;
  font-weight: 500;
}

.report-unmatched ul {
  margin: 0.4rem 0 0;
  padding-left: 1.1rem;
  line-height: 1.65;
}

.report-unmatched p {
  margin-top: 0.2rem;
  opacity: 0.75;
}

.report-table-wrap {
  max-height: 240px;
  margin-top: 0.45rem;
  overflow: auto;
  border: 1px solid rgba(35, 79, 63, 0.18);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.6);
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11.5px;
}

.report-table th {
  position: sticky;
  top: 0;
  padding: 0.4rem 0.55rem;
  border-bottom: 1px solid rgba(35, 79, 63, 0.16);
  background: rgba(255, 255, 255, 0.92);
  font-weight: 600;
  text-align: left;
}

.report-table td {
  padding: 0.4rem 0.55rem;
  border-bottom: 1px solid rgba(35, 79, 63, 0.1);
}

.report-table tr:last-child td {
  border-bottom: 0;
}

.report-table .num {
  font-variant-numeric: tabular-nums;
}

.report-export {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.5rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font-size: 11.5px;
  font-weight: 500;
  text-decoration: underline;
  text-underline-offset: 3px;
}
</style>
