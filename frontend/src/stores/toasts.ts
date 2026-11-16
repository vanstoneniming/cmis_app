import { defineStore } from 'pinia'

export type ToastTone = 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  tone: ToastTone
  title: string
  message?: string
}

let nextId = 1
const timers = new Map<number, ReturnType<typeof setTimeout>>()

export const useToastStore = defineStore('toasts', {
  state: () => ({
    items: [] as ToastItem[],
  }),
  actions: {
    push(tone: ToastTone, title: string, message?: string, duration = 4200) {
      const id = nextId
      nextId += 1
      this.items.push({ id, tone, title, message })
      const timer = setTimeout(() => {
        this.dismiss(id)
      }, duration)
      timers.set(id, timer)
      return id
    },
    success(title: string, message?: string) {
      return this.push('success', title, message)
    },
    error(title: string, message?: string) {
      return this.push('error', title, message, 6000)
    },
    info(title: string, message?: string) {
      return this.push('info', title, message)
    },
    dismiss(id: number) {
      const timer = timers.get(id)
      if (timer) clearTimeout(timer)
      timers.delete(id)
      this.items = this.items.filter((item) => item.id !== id)
    },
  },
})
