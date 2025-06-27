<template>
  <div
    class="timeline-item"
    :class="{
      'timeline-item-llm': isLLMCall,
      'timeline-item-tool': isToolCall,
      'timeline-item-agent': isAgentExecution,
    }"
  >
    <div class="timeline-header" @click="$emit('toggle')">
      <div class="timeline-icon">
        <span v-if="isLLMCall">🤖</span>
        <span v-else-if="isToolCall">🔧</span>
        <span v-else>📝</span>
      </div>
      <div class="timeline-title">
        <h4>{{ title }}</h4>
        <span class="timeline-time">{{ duration }}</span>
      </div>
      <div class="timeline-expand">
        <span v-if="isExpanded">▼</span>
        <span v-else>►</span>
      </div>
    </div>

    <div class="timeline-details" v-if="isExpanded">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  duration: string
  isExpanded: boolean
  isLLMCall?: boolean
  isToolCall?: boolean
  isAgentExecution?: boolean
}

withDefaults(defineProps<Props>(), {
  isLLMCall: false,
  isToolCall: false,
  isAgentExecution: false,
})

defineEmits<{
  toggle: []
}>()
</script>

<style scoped>
.timeline-item {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-background);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.timeline-item-llm {
  border-left: 4px solid var(--color-primary, #007acc);
}

.timeline-item-tool {
  border-left: 4px solid var(--color-success, #27ae60);
}

.timeline-item-agent {
  border-left: 4px solid var(--color-warning, #f39c12);
}

.timeline-header {
  display: flex;
  align-items: center;
  padding: 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.timeline-header:hover {
  background-color: var(--color-background-soft);
}

.timeline-icon {
  font-size: 1.2rem;
  margin-right: 0.75rem;
}

.timeline-title {
  flex: 1;
}

.timeline-title h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.timeline-time {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  margin-top: 0.25rem;
  display: block;
}

.timeline-expand {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  transition: transform 0.2s ease;
}

.timeline-details {
  border-top: 1px solid var(--color-border);
  background-color: var(--color-background-soft);
  padding: 1rem;
}
</style>
