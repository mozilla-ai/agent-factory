<template>
  <div class="code-block-container" :class="{ 'code-block-soft': variant === 'soft' }">
    <div v-if="title" class="code-header">
      <h5>{{ title }}</h5>
      <slot name="actions" />
    </div>

    <pre
      class="code-block"
      :class="{
        'code-scrollable': scrollable,
        'code-wrap': wrap,
      }"
    ><slot>{{ content }}</slot></pre>
  </div>
</template>

<script setup lang="ts">
interface Props {
  content?: string
  title?: string
  scrollable?: boolean
  wrap?: boolean
  maxHeight?: string
  variant?: 'default' | 'soft'
}

withDefaults(defineProps<Props>(), {
  scrollable: true,
  wrap: true,
  maxHeight: '300px',
  variant: 'default',
})
</script>

<style scoped>
.code-block-container {
  background: var(--color-background);
  border-radius: 4px;
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.code-block-container.code-block-soft {
  background: var(--color-background-soft);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: var(--color-background-mute);
  border-bottom: 1px solid var(--color-border);
}

.code-header h5 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text);
}

.code-block {
  margin: 0;
  padding: 0.75rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9rem;
  line-height: 1.4;
  color: var(--color-text);
  background: transparent;
}

.code-block.code-scrollable {
  overflow: auto;
  max-height: v-bind(maxHeight);
}

.code-block.code-wrap {
  white-space: pre-wrap;
  word-break: break-word;
}

.code-block:not(.code-wrap) {
  white-space: pre;
  overflow-x: auto;
}
</style>
