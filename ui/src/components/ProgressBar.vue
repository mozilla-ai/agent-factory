<template>
  <div class="progress-container">
    <div v-if="showLabel" class="progress-header">
      <span class="progress-label">{{ label }}</span>
      <span v-if="showPercentage" class="progress-percentage">{{ Math.round(percentage) }}%</span>
    </div>
    <div class="progress-bar" :class="variant">
      <div class="progress-fill" :style="{ width: `${percentage}%` }" :class="colorClass"></div>
    </div>
    <div v-if="description" class="progress-description">{{ description }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  percentage: number
  label?: string
  description?: string
  variant?: 'default' | 'score' | 'mini'
  colorThreshold?: 'auto' | 'success' | 'warning' | 'error'
  showLabel?: boolean
  showPercentage?: boolean
}>()

const colorClass = computed(() => {
  if (props.colorThreshold === 'auto') {
    if (props.percentage >= 80) return 'progress-success'
    if (props.percentage >= 50) return 'progress-warning'
    return 'progress-error'
  }
  return `progress-${props.colorThreshold || 'success'}`
})
</script>

<style scoped>
.progress-container {
  width: 100%;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.progress-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text);
}

.progress-percentage {
  font-size: 0.8rem;
  color: var(--color-text-light);
}

.progress-bar {
  background: var(--color-background-mute);
  border-radius: 4px;
  overflow: hidden;
  height: 8px;
}

.progress-bar.score {
  height: 12px;
}

.progress-bar.mini {
  height: 4px;
}

.progress-fill {
  height: 100%;
  transition: width 0.5s ease;
}

.progress-success {
  background: linear-gradient(90deg, var(--color-success), var(--color-success-hover));
}

.progress-warning {
  background: linear-gradient(90deg, var(--color-warning), var(--color-warning-hover));
}

.progress-error {
  background: linear-gradient(90deg, var(--color-error), var(--color-error-hover));
}

.progress-description {
  font-size: 0.75rem;
  color: var(--color-text-light);
  margin-top: 0.25rem;
  text-align: right;
}
</style>
