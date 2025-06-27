<template>
  <div class="status-message" :class="variant">
    <div v-if="icon" class="status-icon">{{ icon }}</div>
    <div class="status-content">
      <h3 v-if="title" class="status-title">{{ title }}</h3>
      <p class="status-text">{{ message }}</p>
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  variant: 'loading' | 'error' | 'empty' | 'success'
  message: string
  title?: string
  icon?: string
}>()
</script>

<style scoped>
.status-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  gap: 1rem;
}

.status-message.loading {
  color: var(--color-text-light);
  font-style: italic;
}

.status-message.error {
  color: var(--color-error);
}

.status-message.empty {
  color: var(--color-text-light);
}

.status-message.success {
  color: var(--color-success);
}

.status-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.status-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.status-text {
  margin: 0;
  line-height: 1.5;
}

.status-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
</style>
