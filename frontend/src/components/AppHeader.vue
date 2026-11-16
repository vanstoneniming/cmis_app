<script setup lang="ts">
import { Download, Trash2 } from 'lucide-vue-next'

defineProps<{
  hasData: boolean
  studentCount: number
  rosterFileName: string
}>()

defineEmits<{
  export: []
  clear: []
}>()
</script>

<template>
  <header class="masthead">
    <div class="masthead-inner">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true"><span>合</span></div>
        <div class="brand-copy">
          <h1>CMIS 数据合并台</h1>
          <p>姓名与学号自动匹配，顺序不同也能合并</p>
        </div>
      </div>

      <div class="masthead-meta">
        <span class="local-badge">
          <span class="local-dot" aria-hidden="true"></span>
          本地处理 · 数据不出浏览器
        </span>
        <span v-if="hasData" class="session-note">
          {{ studentCount }} 名学生<template v-if="rosterFileName"> · {{ rosterFileName }}</template>
        </span>
      </div>

      <div class="masthead-actions">
        <button
          v-if="hasData"
          class="btn btn-primary btn-sm"
          type="button"
          data-testid="header-export"
          @click="$emit('export')"
        >
          <Download :size="15" />
          导出 Excel
        </button>
        <button
          v-if="hasData"
          class="icon-btn"
          type="button"
          title="清空当前会话"
          aria-label="清空当前会话"
          @click="$emit('clear')"
        >
          <Trash2 :size="17" />
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.masthead {
  position: sticky;
  top: 0;
  z-index: 30;
  border-bottom: 1px solid rgba(198, 209, 199, 0.75);
  background: rgba(243, 245, 241, 0.9);
  backdrop-filter: blur(14px);
}

.masthead-inner {
  display: flex;
  align-items: center;
  gap: 1.4rem;
  width: min(1480px, 100%);
  margin: 0 auto;
  padding: 0.75rem 1.75rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-width: 0;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 39px;
  height: 39px;
  flex: none;
  border-radius: 10px;
  background: var(--pine);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.14);
  color: #f4f8f4;
  font-family: var(--font-display);
  font-size: 21px;
  line-height: 1;
}

.brand-copy {
  min-width: 0;
}

.brand-copy h1 {
  font-size: 19px;
  line-height: 1.2;
  white-space: nowrap;
}

.brand-copy p {
  margin-top: 0.1rem;
  color: var(--muted);
  font-size: 11.5px;
  white-space: nowrap;
}

.masthead-meta {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  min-width: 0;
  margin-left: auto;
}

.local-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  height: 27px;
  padding: 0 0.65rem;
  border: 1px solid #c7ded1;
  border-radius: 999px;
  background: #eef6f1;
  color: #2b5c49;
  font-size: 11.5px;
  white-space: nowrap;
}

.local-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3f8b6f;
  box-shadow: 0 0 0 3px rgba(63, 139, 111, 0.13);
}

.session-note {
  max-width: 280px;
  overflow: hidden;
  color: var(--muted);
  font-size: 11.5px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.masthead-actions {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-left: 0.2rem;
}

@media (max-width: 1080px) {
  .session-note {
    display: none;
  }
}

@media (max-width: 820px) {
  .masthead-inner {
    padding: 0.65rem 1rem;
    gap: 0.7rem;
  }

  .brand-copy p {
    display: none;
  }

  .brand-copy h1 {
    font-size: 17px;
  }

  .local-badge {
    display: none;
  }

  .masthead-meta {
    margin-left: auto;
  }
}

@media (max-width: 520px) {
  .brand-mark {
    width: 34px;
    height: 34px;
    font-size: 18px;
  }

  .brand-copy h1 {
    font-size: 15.5px;
  }

  .masthead-actions .icon-btn {
    display: none;
  }
}
</style>
