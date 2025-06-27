<template>
  <div class="score-card">
    <div class="score-header">
      <div class="score-title-row">
        <h3 class="score-title">{{ title }}</h3>
        <slot name="actions"></slot>
      </div>
      <div v-if="description" class="score-description">{{ description }}</div>
    </div>

    <div class="score-value">{{ score }} / {{ maxScore }}</div>
    <div class="score-percentage">{{ Math.round(percentage) }}%</div>

    <ProgressBar :percentage="percentage" variant="score" :color-threshold="colorThreshold" />

    <slot name="content"></slot>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ProgressBar from './ProgressBar.vue'

const props = defineProps<{
  title: string
  description?: string
  score: number
  maxScore: number
  colorThreshold?: 'auto' | 'success' | 'warning' | 'error'
}>()

const percentage = computed(() => (props.maxScore > 0 ? (props.score / props.maxScore) * 100 : 0))
</script>

<style scoped>
.score-card {
  background: var(--color-background-soft);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--color-border);
}

.score-header {
  margin-bottom: 1rem;
}

.score-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-heading);
}

.score-description {
  font-size: 0.875rem;
  color: var(--color-text-light);
  margin-top: 0.25rem;
}

.score-value {
  font-size: 2rem;
  font-weight: 700;
  margin: 0.5rem 0;
  color: var(--color-text);
}

.score-percentage {
  font-size: 0.875rem;
  color: var(--color-text-light);
  margin-bottom: 0.75rem;
}
</style>
