<template>
  <div v-if="isOpen" class="confirmation-overlay">
    <div class="confirmation-dialog" role="dialog" aria-modal="true">
      <div class="dialog-header">
        <h3 class="dialog-title">{{ title }}</h3>
        <button class="close-button" @click="cancel" aria-label="Close">×</button>
      </div>

      <div class="dialog-content">
        <p class="dialog-message">{{ message }}</p>
      </div>

      <div class="dialog-actions">
        <button class="cancel-button" @click="cancel" :disabled="isLoading">Cancel</button>
        <button
          class="confirm-button"
          :class="{ danger: isDangerous }"
          @click="confirm"
          :disabled="isLoading"
        >
          {{ confirmButtonText }}
          <span v-if="isLoading" class="loading-spinner"></span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  isOpen: boolean
  title: string
  message: string
  confirmButtonText: string
  isDangerous?: boolean
  isLoading?: boolean
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

function confirm() {
  emit('confirm')
}

function cancel() {
  emit('cancel')
}
</script>

<style scoped>
.confirmation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.confirmation-dialog {
  background-color: var(--color-background);
  border-radius: 8px;
  width: 90%;
  max-width: 450px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.dialog-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.5rem;
  color: var(--color-text-light);
}

.dialog-content {
  padding: 1.5rem;
}

.dialog-message {
  margin: 0;
  line-height: 1.5;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  padding: 1rem 1.5rem;
  gap: 1rem;
  border-top: 1px solid var(--color-border);
}

.cancel-button {
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background-color: var(--color-background);
  color: var(--color-text);
  font-weight: 500;
  cursor: pointer;
}

.cancel-button:hover:not(:disabled) {
  background-color: var(--color-background-soft);
}

.confirm-button {
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  border: none;
  background-color: var(--color-primary);
  color: white;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.confirm-button.danger {
  background-color: var(--color-error);
}

.confirm-button:hover:not(:disabled) {
  opacity: 0.9;
}

.confirm-button:disabled,
.cancel-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
