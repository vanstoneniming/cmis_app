<script setup lang="ts">
import { computed } from 'vue'
import type { DataRow } from '../types'
import { displayCell } from '../lib/cells'

const props = withDefaults(
  defineProps<{
    columns: string[]
    rows: DataRow[]
    limit?: number
    caption?: string
    testId?: string
  }>(),
  {
    limit: 10,
    caption: '',
    testId: 'preview-table',
  },
)

const visibleRows = computed(() => props.rows.slice(0, props.limit))
const hiddenCount = computed(() => Math.max(0, props.rows.length - props.limit))
</script>

<template>
  <div class="preview" :data-testid="testId">
    <div v-if="columns.length === 0" class="preview-empty">
      暂时没有可预览的数据
    </div>
    <template v-else>
      <div class="preview-scroll">
        <table>
          <thead>
            <tr>
              <th class="row-no">#</th>
              <th v-for="column in columns" :key="column">{{ column }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in visibleRows" :key="index">
              <td class="row-no">{{ index + 1 }}</td>
              <td v-for="column in columns" :key="column" :title="displayCell(row[column] ?? null)">
                {{ displayCell(row[column] ?? null) || '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="preview-caption">
        <span>{{ caption || `显示前 ${Math.min(limit, rows.length)} 行，共 ${rows.length} 行` }}</span>
        <span v-if="hiddenCount > 0">还有 {{ hiddenCount }} 行未显示</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.preview {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
}

.preview-scroll {
  max-height: 230px;
  overflow: auto;
}

table {
  width: max-content;
  min-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 12px;
}

th,
td {
  max-width: 220px;
  padding: 0.45rem 0.65rem;
  border-bottom: 1px solid var(--line);
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--surface-soft);
  color: var(--ink-soft);
  font-size: 11.5px;
  font-weight: 600;
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr:hover td {
  background: #fbfcf9;
}

.row-no {
  width: 44px;
  min-width: 44px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.preview-caption {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.45rem 0.65rem;
  border-top: 1px solid var(--line);
  background: var(--surface-soft);
  color: var(--muted);
  font-size: 11px;
}

.preview-empty {
  padding: 2.2rem 1rem;
  color: var(--muted);
  font-size: 12.5px;
  text-align: center;
}
</style>
