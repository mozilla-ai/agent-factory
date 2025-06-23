<template>
  <div class="streaming-output">
    <div class="output-header">
      <h3>{{ title }}</h3>
      <slot name="actions" />
    </div>

    <div v-if="isLoading && !content" class="loading-state">
      <span class="loading-indicator">{{ loadingText }}</span>
    </div>

    <div v-else-if="!isLoading && !content" class="empty-state">
      {{ emptyMessage }}
    </div>

    <div v-if="content" class="content-container">
      <CodeBlock :content="content" :scrollable="true" :max-height="maxHeight" :wrap="true" />

      <!-- Show loading indicator while streaming -->
      <div v-if="isLoading" class="streaming-indicator">
        <span class="loading-indicator">Streaming...</span>
        <div class="streaming-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>

    <div v-if="$slots.footer" class="output-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import CodeBlock from './CodeBlock.vue'

interface Props {
  title?: string
  content?: string
  isLoading?: boolean
  loadingText?: string
  emptyMessage?: string
  maxHeight?: string
}

withDefaults(defineProps<Props>(), {
  title: 'Output',
  loadingText: 'Processing...',
  emptyMessage: 'This is where the output will be displayed.',
  maxHeight: '400px',
})
</script>

<style scoped>
.streaming-output {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.output-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.loading-state {
  display: flex;
  align-items: center;
  padding: 1rem;
  font-style: italic;
  color: var(--color-text-light);
  background: var(--color-background-soft);
  border-radius: 4px;
  border: 1px solid var(--color-border);
}

.loading-indicator::before {
  content: '⏳ ';
  margin-right: 0.5rem;
}

.empty-state {
  padding: 1rem;
  color: var(--color-text-light);
  font-style: italic;
  text-align: center;
}

.content-container {
  position: relative;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border-radius: 0 0 4px 4px;
  border: 1px solid var(--color-primary-soft);
  border-top: none;
  margin-top: -1px; /* Overlap with CodeBlock border */
  font-style: italic;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.streaming-dots {
  display: flex;
  gap: 0.2rem;
}

.streaming-dots span {
  width: 0.25rem;
  height: 0.25rem;
  background: var(--color-primary);
  border-radius: 50%;
  animation: streaming-pulse 1.5s infinite;
}

.streaming-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.streaming-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes streaming-pulse {
  0%,
  60%,
  100% {
    opacity: 0.3;
    transform: scale(1);
  }
  30% {
    opacity: 1;
    transform: scale(1.2);
  }
}

.output-footer {
  margin-top: 0.5rem;
}
</style>
