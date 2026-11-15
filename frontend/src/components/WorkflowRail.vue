<script setup lang="ts">
import { ArrowRight, Check, Download, Layers, Trash2 } from 'lucide-vue-next'
import FileDropzone from './FileDropzone.vue'

defineProps<{
  hasData: boolean
  studentCount: number
  rosterFileName: string
  dataColumnCount: number
}>()

defineEmits<{
  'roster-file': [file: File]
  'open-merge': []
  export: []
  clear: []
}>()
</script>

<template>
  <aside class="rail">
    <div class="rail-head">
      <h2>工作流程</h2>
      <p>按顺序完成三步，数据始终留在本机。</p>
    </div>

    <ol class="steps">
      <li class="step" :class="{ done: hasData }">
        <span class="step-marker" aria-hidden="true">
          <Check v-if="hasData" :size="14" :stroke-width="2.4" />
          <span v-else>01</span>
        </span>
        <div class="step-body">
          <h3>导入名单</h3>
          <p class="step-desc">选择基准 Excel，确认姓名与学号列。</p>
          <div v-if="rosterFileName" class="file-chip">
            <span class="file-name">{{ rosterFileName }}</span>
            <span class="file-count">{{ studentCount }} 人</span>
          </div>
          <FileDropzone
            compact
            tone="dark"
            :label="hasData ? '换一份基准名单' : '选择基准 Excel'"
            hint=".xlsx / .xls"
            test-id="rail-roster-input"
            @select="$emit('roster-file', $event)"
          />
        </div>
      </li>

      <li class="step" :class="{ done: dataColumnCount > 0, locked: !hasData }">
        <span class="step-marker" aria-hidden="true">
          <Check v-if="dataColumnCount > 0" :size="14" :stroke-width="2.4" />
          <span v-else>02</span>
        </span>
        <div class="step-body">
          <h3>合并数据</h3>
          <p class="step-desc">上传第二份 Excel，选择要并入的数据列。</p>
          <button
            class="rail-action"
            type="button"
            :disabled="!hasData"
            data-testid="rail-open-merge"
            @click="$emit('open-merge')"
          >
            <Layers :size="16" />
            <span>打开合并面板</span>
            <ArrowRight class="rail-action-arrow" :size="15" />
          </button>
          <p v-if="dataColumnCount > 0" class="step-note">已并入 {{ dataColumnCount }} 个数据列</p>
          <p v-else-if="!hasData" class="step-note">先完成第 1 步</p>
        </div>
      </li>

      <li class="step" :class="{ locked: !hasData }">
        <span class="step-marker" aria-hidden="true">03</span>
        <div class="step-body">
          <h3>校对导出</h3>
          <p class="step-desc">在表格中直接修改，最后导出 Excel。</p>
          <button
            class="rail-action rail-action-light"
            type="button"
            :disabled="!hasData"
            data-testid="rail-export"
            @click="$emit('export')"
          >
            <Download :size="16" />
            <span>导出 Excel</span>
          </button>
        </div>
      </li>
    </ol>

    <div class="rail-footer">
      <p>数据只保存在当前浏览器标签页，关闭后清空。</p>
      <button
        v-if="hasData"
        class="rail-clear"
        type="button"
        @click="$emit('clear')"
      >
        <Trash2 :size="13" />
        清空当前会话
      </button>
    </div>
  </aside>
</template>

<style scoped>
.rail {
  position: relative;
  overflow: hidden;
  padding: 1.35rem 1.15rem 1.1rem;
  border-radius: var(--radius-lg);
  background:
    radial-gradient(ellipse at 100% 0%, rgba(159, 196, 181, 0.18), transparent 46%),
    linear-gradient(158deg, #0f4a3d 0%, #0a372d 78%);
  box-shadow: 0 22px 46px rgba(10, 45, 35, 0.18);
  color: #eef5f0;
}

.rail::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image: linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px);
  background-size: 100% 28px;
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.5), transparent 70%);
}

.rail-head {
  position: relative;
  z-index: 1;
  margin-bottom: 1.3rem;
}

.rail-head h2 {
  color: #f4f9f6;
  font-size: 19px;
}

.rail-head p {
  margin-top: 0.2rem;
  color: rgba(232, 243, 237, 0.62);
  font-size: 11.5px;
}

.steps {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 1.3rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.steps::before {
  content: '';
  position: absolute;
  top: 27px;
  bottom: 20px;
  left: 13px;
  width: 1px;
  background: rgba(255, 255, 255, 0.17);
}

.step {
  position: relative;
  display: flex;
  gap: 0.75rem;
}

.step-marker {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 27px;
  height: 27px;
  flex: none;
  border: 1px solid rgba(255, 255, 255, 0.26);
  border-radius: 8px;
  background: #0c4034;
  color: rgba(238, 247, 241, 0.74);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.step.done .step-marker {
  border-color: var(--celadon);
  background: var(--celadon);
  color: var(--pine-deep);
}

.step-body {
  min-width: 0;
  flex: 1;
  padding-top: 0.05rem;
}

.step-body h3 {
  color: #f1f7f3;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0;
}

.step-desc {
  margin-top: 0.16rem;
  color: rgba(232, 243, 237, 0.58);
  font-size: 11.5px;
  line-height: 1.5;
}

.step.locked .step-body {
  opacity: 0.55;
}

.file-chip {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin: 0.55rem 0 0.45rem;
  padding: 0.38rem 0.55rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.07);
  font-size: 11px;
}

.file-name {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: #e7f2ec;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-count {
  flex: none;
  color: rgba(232, 243, 237, 0.58);
}

.rail-action {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  width: 100%;
  height: 36px;
  margin-top: 0.55rem;
  padding: 0 0.65rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
  color: #e9f4ee;
  font-size: 12.5px;
  font-weight: 500;
  text-align: left;
  transition:
    background-color 160ms ease,
    border-color 160ms ease;
}

.rail-action:hover:not(:disabled) {
  border-color: rgba(255, 255, 255, 0.38);
  background: rgba(255, 255, 255, 0.13);
}

.rail-action:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.rail-action-arrow {
  margin-left: auto;
  opacity: 0.6;
}

.rail-action-light {
  border-color: #e8f0ea;
  background: #f2f7f3;
  color: var(--pine-deep);
}

.rail-action-light:hover:not(:disabled) {
  border-color: #ffffff;
  background: #ffffff;
}

.step-note {
  margin-top: 0.35rem;
  color: rgba(159, 196, 181, 0.85);
  font-size: 10.5px;
}

.rail-footer {
  position: relative;
  z-index: 1;
  margin-top: 1.5rem;
  padding-top: 0.85rem;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.rail-footer p {
  color: rgba(232, 243, 237, 0.45);
  font-size: 10.5px;
  line-height: 1.5;
}

.rail-clear {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.5rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: rgba(240, 200, 194, 0.8);
  font-size: 11px;
}

.rail-clear:hover {
  color: #f3c7c0;
}

@media (max-width: 980px) {
  .rail {
    padding: 1.1rem 1rem 0.9rem;
  }

  .steps {
    gap: 1rem;
  }

  .rail-head {
    margin-bottom: 0.9rem;
  }
}
</style>
