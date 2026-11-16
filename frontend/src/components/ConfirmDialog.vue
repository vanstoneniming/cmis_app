<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, useId } from 'vue'
import { AlertTriangle, X } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    title: string
    message: string
    confirmLabel?: string
    cancelLabel?: string
    tone?: 'danger' | 'primary'
  }>(),
  {
    confirmLabel: '确认',
    cancelLabel: '取消',
    tone: 'primary',
  },
)

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const titleId = useId()
const panel = ref<HTMLElement | null>(null)
let previousOverflow = ''

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('cancel')
}

onMounted(() => {
  previousOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  document.addEventListener('keydown', onKeydown)
  window.setTimeout(() => panel.value?.focus(), 20)
})

onBeforeUnmount(() => {
  document.body.style.overflow = previousOverflow
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div class="confirm-backdrop" @click.self="$emit('cancel')">
      <section
        ref="panel"
        class="confirm-panel"
        role="alertdialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        tabindex="-1"
        data-testid="confirm-dialog"
      >
        <div class="confirm-icon" :class="`is-${props.tone}`">
          <AlertTriangle :size="20" />
        </div>
        <div class="confirm-body">
          <h2 :id="titleId">{{ title }}</h2>
          <p>{{ message }}</p>
        </div>
        <button class="icon-btn confirm-close" type="button" aria-label="关闭" @click="$emit('cancel')">
          <X :size="17" />
        </button>
        <div class="confirm-actions">
          <button class="btn btn-secondary btn-sm" type="button" data-testid="confirm-cancel" @click="$emit('cancel')">
            {{ cancelLabel }}
          </button>
          <button
            class="btn btn-sm"
            :class="props.tone === 'danger' ? 'btn-danger' : 'btn-primary'"
            type="button"
            data-testid="confirm-ok"
            @click="$emit('confirm')"
          >
            {{ confirmLabel }}
          </button>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.confirm-backdrop {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(8, 26, 20, 0.46);
  backdrop-filter: blur(2px);
  animation: confirm-fade 160ms ease both;
}

.confirm-panel {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.75rem;
  width: min(430px, 100%);
  padding: 1.2rem 1.25rem 1.1rem;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--surface);
  box-shadow: 0 24px 60px rgba(8, 26, 20, 0.28);
  animation: confirm-in 180ms cubic-bezier(0.22, 0.8, 0.26, 1) both;
}

.confirm-panel:focus {
  outline: none;
}

.confirm-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--seal-bg);
  color: var(--seal);
}

.confirm-icon.is-primary {
  background: var(--mint);
  color: var(--pine-soft);
}

.confirm-body h2 {
  padding-right: 1.8rem;
  font-family: var(--font-body);
  font-size: 15.5px;
  font-weight: 600;
  letter-spacing: 0;
}

.confirm-body p {
  margin-top: 0.35rem;
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.6;
}

.confirm-close {
  position: absolute;
  top: 0.65rem;
  right: 0.65rem;
  width: 30px;
  height: 30px;
}

.confirm-actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.35rem;
}

@keyframes confirm-fade {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes confirm-in {
  from {
    transform: translateY(6px) scale(0.985);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}
</style>
