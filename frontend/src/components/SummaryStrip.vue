<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  students: number
  classes: number
  dataColumns: number
  completeness: number | null
}>()

const percent = computed(() =>
  props.completeness === null ? null : Math.round(props.completeness * 100),
)
</script>

<template>
  <section class="summary-strip" aria-label="数据概况">
    <div class="stat">
      <span class="stat-label">学生</span>
      <span class="stat-value num">{{ students }}</span>
    </div>
    <div class="stat">
      <span class="stat-label">班级</span>
      <span class="stat-value num">{{ classes }}</span>
    </div>
    <div class="stat">
      <span class="stat-label">数据列</span>
      <span class="stat-value num">{{ dataColumns }}</span>
    </div>
    <div class="stat stat-complete">
      <span class="stat-label">数据完整度</span>
      <span class="stat-value num">{{ percent === null ? '—' : `${percent}%` }}</span>
      <span class="meter" aria-hidden="true">
        <span class="meter-fill" :style="{ width: `${percent ?? 0}%` }"></span>
      </span>
    </div>
  </section>
</template>

<style scoped>
.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(80px, 0.7fr)) minmax(140px, 1.1fr);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}

.stat {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
  padding: 1rem 1.2rem 1.05rem;
}

.stat + .stat::before {
  content: '';
  position: absolute;
  top: 20%;
  bottom: 20%;
  left: 0;
  width: 1px;
  background: var(--line);
}

.stat-label {
  color: var(--muted);
  font-size: 11.5px;
  font-weight: 500;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 27px;
  line-height: 1.1;
  color: var(--ink);
}

.stat-complete {
  padding-right: 1.35rem;
}

.meter {
  display: block;
  width: 100%;
  height: 3px;
  margin-top: 0.45rem;
  overflow: hidden;
  border-radius: 999px;
  background: var(--line);
}

.meter-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--pine-soft), var(--celadon));
  transition: width 320ms ease;
}

@media (max-width: 700px) {
  .summary-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat + .stat::before {
    display: none;
  }

  .stat:nth-child(even)::before {
    display: block;
  }

  .stat:nth-child(n + 3) {
    border-top: 1px solid var(--line);
  }

  .stat {
    padding: 0.8rem 1rem;
  }

  .stat-value {
    font-size: 23px;
  }
}
</style>
