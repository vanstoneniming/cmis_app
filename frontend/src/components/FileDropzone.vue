<script setup lang="ts">
import { ref } from 'vue'
import { AlertCircle, ChevronRight, FileSpreadsheet, UploadCloud } from 'lucide-vue-next'
import { isExcelFile } from '../lib/excel'

const props = withDefaults(
  defineProps<{
    label: string
    hint?: string
    compact?: boolean
    tone?: 'light' | 'dark'
    disabled?: boolean
    testId?: string
  }>(),
  {
    hint: '支持 .xlsx / .xls',
    compact: false,
    tone: 'light',
    disabled: false,
    testId: 'file-input',
  },
)

const emit = defineEmits<{
  select: [file: File]
  error: [message: string]
}>()

const input = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const localError = ref('')

function acceptFile(file: File | undefined) {
  localError.value = ''
  if (!file) return
  if (!isExcelFile(file)) {
    localError.value = '请选择 .xlsx 或 .xls 文件'
    emit('error', localError.value)
    return
  }
  emit('select', file)
  if (input.value) input.value.value = ''
}

function onChange(event: Event) {
  const target = event.target as HTMLInputElement
  acceptFile(target.files?.[0])
}

function onDrop(event: DragEvent) {
  event.preventDefault()
  dragging.value = false
  if (props.disabled) return
  acceptFile(event.dataTransfer?.files?.[0])
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (!props.disabled) dragging.value = true
}

function onDragLeave(event: DragEvent) {
  if (event.currentTarget === event.target) dragging.value = false
}

</script>

<template>
  <div class="dropzone-wrap" :class="{ 'is-compact': compact, 'is-dark': tone === 'dark' }">
    <label
      class="dropzone"
      :class="{ 'is-dragging': dragging, 'is-disabled': disabled }"
      :data-testid="`${testId}-zone`"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <input
        ref="input"
        type="file"
        class="sr-only"
        accept=".xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
        :disabled="disabled"
        :data-testid="testId"
        @change="onChange"
      />
      <span class="dz-icon">
        <UploadCloud v-if="compact" :size="18" :stroke-width="1.8" />
        <FileSpreadsheet v-else :size="30" :stroke-width="1.5" />
      </span>
      <span class="dz-copy">
        <strong>{{ label }}</strong>
        <span>{{ hint }}</span>
      </span>
      <ChevronRight v-if="compact" class="dz-chevron" :size="17" :stroke-width="1.8" />
      <span v-else class="dz-browse">浏览文件</span>
    </label>
    <p v-if="localError" class="dz-error">
      <AlertCircle :size="13" />
      {{ localError }}
    </p>
  </div>
</template>

<style scoped>
.dropzone-wrap {
  width: 100%;
}

.dropzone {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.75rem;
  min-height: 138px;
  padding: 1.2rem 1.25rem;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.72);
  cursor: pointer;
  transition:
    border-color 160ms ease,
    background-color 160ms ease,
    box-shadow 160ms ease;
}

.dropzone:hover {
  border-color: var(--pine-soft);
  background: var(--surface);
  box-shadow: 0 8px 24px rgba(13, 74, 61, 0.07);
}

.dropzone:focus-within {
  outline: 2px solid var(--pine-soft);
  outline-offset: 2px;
}

.dropzone.is-dragging {
  border-color: var(--pine-soft);
  border-style: solid;
  background: var(--mint);
  box-shadow: 0 0 0 3px rgba(26, 107, 88, 0.1);
}

.dropzone.is-disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.dz-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--mint);
  color: var(--pine);
}

.dz-copy {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.dz-copy strong {
  font-size: 14.5px;
  font-weight: 600;
  color: var(--ink);
}

.dz-copy span {
  color: var(--muted);
  font-size: 12px;
}

.dz-browse {
  display: inline-flex;
  align-items: center;
  height: 28px;
  margin-top: auto;
  padding: 0 0.65rem;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: var(--surface);
  color: var(--ink-soft);
  font-size: 12px;
}

.is-compact .dropzone {
  flex-direction: row;
  align-items: center;
  min-height: 0;
  gap: 0.6rem;
  padding: 0.65rem 0.7rem;
  border-radius: 9px;
}

.is-compact .dz-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
}

.is-compact .dz-copy {
  min-width: 0;
  flex: 1;
}

.is-compact .dz-copy strong {
  font-size: 12.5px;
}

.is-compact .dz-copy span {
  font-size: 11px;
}

.dz-chevron {
  color: var(--muted);
}

.dz-error {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.45rem;
  color: var(--seal);
  font-size: 11.5px;
}

.is-dark .dropzone {
  border-color: rgba(255, 255, 255, 0.24);
  background: rgba(255, 255, 255, 0.06);
}

.is-dark .dropzone:hover {
  border-color: rgba(255, 255, 255, 0.52);
  background: rgba(255, 255, 255, 0.1);
  box-shadow: none;
}

.is-dark .dropzone.is-dragging {
  border-color: var(--celadon);
  background: rgba(159, 196, 181, 0.16);
  box-shadow: 0 0 0 3px rgba(159, 196, 181, 0.12);
}

.is-dark .dz-icon {
  background: rgba(255, 255, 255, 0.11);
  color: #d7e9e0;
}

.is-dark .dz-copy strong {
  color: #f1f7f3;
}

.is-dark .dz-copy span,
.is-dark .dz-chevron {
  color: rgba(232, 243, 237, 0.62);
}

.is-dark .dz-browse {
  border-color: rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.08);
  color: #e7f2ec;
}

.is-dark .dz-error {
  color: #f0b9b1;
}
</style>
