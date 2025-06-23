<template>
  <div class="stat-item" :class="variant">
    <span class="stat-label">{{ label }}</span>
    <span class="stat-value">
      <slot>{{ value }}</slot>
    </span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  label: string
  value?: string | number
  variant?: 'default' | 'metric'
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
})
</script>

<style scoped>
.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--color-text-light, var(--color-text-secondary));
}

.stat-value {
  font-size: 1.2rem;
  font-weight: 500;
}

/* Metric variant for smaller, inline metrics */
.stat-item.metric {
  gap: 0.25rem;
}

.stat-item.metric .stat-label {
  font-size: 0.8rem;
}

.stat-item.metric .stat-value {
  font-size: 1rem;
  font-weight: 500;
}
</style>
