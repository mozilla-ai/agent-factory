<template>
  <div class="eval-file-card">
    <div class="card-header">
      <h4>{{ title }}</h4>
    </div>
    <div class="card-content">
      <p>{{ description }}</p>
      <slot></slot>
    </div>
    <div v-if="showActions" class="card-actions">
      <slot name="actions">
        <button v-if="actionLabel" class="view-button" @click="$emit('action')">
          {{ actionLabel }}
        </button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description: string
  actionLabel?: string
  showActions?: boolean
}>()

defineEmits<{
  action: []
}>()
</script>

<style scoped>
.eval-file-card {
  background: var(--color-background-soft);
  border-radius: 8px;
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card-header {
  font-size: 1.125rem;
  font-weight: 500;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-mute);
}

.card-header h4 {
  margin: 0;
}

.card-content {
  font-size: 0.875rem;
  color: var(--color-text);
  padding: 1rem;
  flex: 1;
}

.card-content p {
  margin: 0 0 1rem 0;
  line-height: 1.5;
}

.card-actions {
  padding: 1rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-background-mute);
}

.view-button {
  background: var(--button-background-color);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  width: 100%;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.view-button:hover {
  background: var(--button-hover-color);
}

.view-button:active {
  background: var(--button-active-color);
}
</style>
