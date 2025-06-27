<template>
  <div class="section-card" :class="variant">
    <div v-if="title || $slots.header" class="section-header">
      <h5 v-if="title">{{ title }}</h5>
      <slot name="header" />
    </div>

    <div class="section-content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  variant?: 'default' | 'metrics' | 'compact'
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
})
</script>

<style scoped>
.section-card {
  margin-bottom: 1rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.section-header h5 {
  margin: 0;
  font-weight: 500;
  color: var(--color-heading, var(--color-text));
}

.section-content {
  /* Default content styling */
}

/* Metrics variant */
.section-card.metrics {
  background-color: var(--color-background);
  border-radius: 4px;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
}

.section-card.metrics .section-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

/* Compact variant */
.section-card.compact {
  margin-bottom: 0.5rem;
}

.section-card.compact .section-header h5 {
  font-size: 0.9rem;
}
</style>
