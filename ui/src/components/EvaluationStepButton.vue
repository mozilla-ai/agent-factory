<template>
  <button
    class="eval-button"
    :class="{
      completed: isCompleted,
      failed: hasError,
    }"
    :disabled="isDisabled"
    @click="$emit('click')"
  >
    <span class="step-number">{{ stepNumber }}</span>
    <div class="step-content">
      <h4>{{ title }}</h4>
      <p>{{ description }}</p>
    </div>
    <div class="step-status">
      <span v-if="isLoading" class="loading-indicator">⏳</span>
      <span v-else-if="hasError" class="error-indicator">✗</span>
      <span v-else-if="isCompleted" class="success-indicator">✓</span>
    </div>
  </button>
</template>

<script setup lang="ts">
interface Props {
  stepNumber: number
  title: string
  description: string
  isCompleted?: boolean
  isLoading?: boolean
  isDisabled?: boolean
  hasError?: boolean
}

withDefaults(defineProps<Props>(), {
  isCompleted: false,
  isLoading: false,
  isDisabled: false,
  hasError: false,
})

defineEmits<{
  click: []
}>()
</script>

<style scoped>
.eval-button {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-background);
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
  width: 100%;
}

.eval-button:not(:disabled):hover {
  border-color: var(--color-border-hover);
  background-color: var(--color-background-hover);
}

.eval-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.eval-button.completed {
  border-color: var(--color-success, green);
  background-color: var(--color-success-background, rgba(0, 128, 0, 0.1));
  box-shadow: 0 0 0 1px var(--color-success, green);
}

.eval-button.failed {
  border-color: var(--color-error, #ef4444);
  background-color: var(--color-error-background, rgba(239, 68, 68, 0.1));
  box-shadow: 0 0 0 1px var(--color-error, #ef4444);
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background-color: var(--color-background-soft);
  color: var(--color-text);
  font-weight: bold;
  border: 1px solid var(--color-border);
}

.step-content {
  flex: 1;
}

.step-content h4 {
  margin: 0 0 0.25rem;
  color: var(--color-heading, var(--color-text));
}

.step-content p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.step-status {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
}

.loading-indicator,
.success-indicator,
.error-indicator {
  font-size: 1.25rem;
}

.success-indicator {
  color: var(--color-success, green);
  font-size: 1.4rem;
}

.error-indicator {
  color: var(--color-error, #ef4444);
  font-size: 1.4rem;
  font-weight: bold;
}
</style>
