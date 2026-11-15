<script setup lang="ts">
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-vue-next'
import { useToastStore } from '../stores/toasts'

const toasts = useToastStore()
</script>

<template>
  <Teleport to="body">
    <div class="toast-stack" aria-live="polite" aria-atomic="false">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts.items"
          :key="toast.id"
          class="toast"
          :class="`toast-${toast.tone}`"
          role="status"
        >
          <CheckCircle2 v-if="toast.tone === 'success'" :size="18" />
          <AlertCircle v-else-if="toast.tone === 'error'" :size="18" />
          <Info v-else :size="18" />
          <div class="toast-copy">
            <strong>{{ toast.title }}</strong>
            <p v-if="toast.message">{{ toast.message }}</p>
          </div>
          <button class="toast-close" type="button" aria-label="关闭通知" @click="toasts.dismiss(toast.id)">
            <X :size="14" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-stack {
  position: fixed;
  top: 82px;
  right: 22px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  width: min(370px, calc(100vw - 32px));
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  padding: 0.8rem 0.85rem;
  border: 1px solid var(--line);
  border-radius: 11px;
  background: var(--surface);
  box-shadow: 0 14px 34px rgba(10, 32, 25, 0.16);
  color: var(--ink-soft);
  pointer-events: auto;
}

.toast svg {
  flex: none;
  margin-top: 1px;
}

.toast-success {
  border-color: #c3dbcc;
  color: #245542;
}

.toast-success svg {
  color: var(--pine-soft);
}

.toast-error {
  border-color: #edc7c2;
  color: #7c2f28;
}

.toast-error svg {
  color: var(--seal);
}

.toast-info {
  border-color: var(--line-strong);
}

.toast-info svg {
  color: var(--pine-soft);
}

.toast-copy {
  min-width: 0;
  flex: 1;
}

.toast-copy strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
}

.toast-copy p {
  margin-top: 0.15rem;
  color: var(--muted);
  font-size: 11.5px;
  line-height: 1.45;
  word-break: break-word;
}

.toast-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin: -0.2rem -0.25rem 0 0;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--muted);
}

.toast-close:hover {
  background: rgba(13, 74, 61, 0.07);
  color: var(--ink);
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 200ms ease,
    transform 200ms ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 640px) {
  .toast-stack {
    top: 72px;
    right: 12px;
  }
}
</style>
