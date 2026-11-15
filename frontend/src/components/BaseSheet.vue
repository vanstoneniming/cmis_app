<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, useId } from 'vue'
import { X } from 'lucide-vue-next'

defineProps<{
  title: string
  subtitle?: string
  testId?: string
}>()

const emit = defineEmits<{ close: [] }>()

const titleId = useId()
const panel = ref<HTMLElement | null>(null)
let previousOverflow = ''

function close() {
  emit('close')
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') close()
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
    <div class="sheet-backdrop" @click.self="close">
      <section
        ref="panel"
        class="sheet-panel"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        tabindex="-1"
        :data-testid="testId"
      >
        <header class="sheet-header">
          <div class="sheet-heading">
            <h2 :id="titleId">{{ title }}</h2>
            <p v-if="subtitle">{{ subtitle }}</p>
          </div>
          <button class="icon-btn sheet-close" type="button" aria-label="关闭" @click="close">
            <X :size="19" />
          </button>
        </header>
        <div class="sheet-body">
          <slot />
        </div>
        <footer v-if="$slots.footer" class="sheet-footer">
          <slot name="footer" />
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.sheet-backdrop {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  justify-content: flex-end;
  background: rgba(8, 26, 20, 0.44);
  backdrop-filter: blur(2px);
  animation: backdrop-in 180ms ease both;
}

.sheet-panel {
  display: flex;
  flex-direction: column;
  width: min(900px, 100vw);
  height: 100dvh;
  background: var(--surface);
  box-shadow: var(--shadow-lg);
  animation: panel-in 240ms cubic-bezier(0.22, 0.8, 0.26, 1) both;
}

.sheet-panel:focus {
  outline: none;
}

.sheet-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.2rem 1.5rem 1rem;
  border-bottom: 1px solid var(--line);
  background: var(--surface);
}

.sheet-heading h2 {
  font-size: 23px;
  line-height: 1.25;
}

.sheet-heading p {
  max-width: 60ch;
  margin-top: 0.3rem;
  color: var(--muted);
  font-size: 12.5px;
}

.sheet-close {
  margin-top: -0.2rem;
}

.sheet-body {
  flex: 1;
  overflow: auto;
  padding: 1.35rem 1.5rem 2rem;
}

.sheet-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1.5rem;
  border-top: 1px solid var(--line);
  background: var(--surface-soft);
}

@keyframes backdrop-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes panel-in {
  from {
    transform: translateX(34px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@media (max-width: 640px) {
  .sheet-header {
    padding: 1rem 1rem 0.85rem;
  }

  .sheet-body {
    padding: 1.1rem 1rem 1.5rem;
  }

  .sheet-footer {
    padding: 0.8rem 1rem;
  }
}
</style>
