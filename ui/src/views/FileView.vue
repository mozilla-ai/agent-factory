<template>
  <div class="file-view">
    <div class="file-nav">
      <button class="back-button" @click="goBack">
        <span class="back-icon">←</span> Back to Workflows
      </button>
    </div>

    <div class="file-header">
      <h2>{{ fileName }}</h2>
      <div class="file-path">{{ filePath }}</div>
    </div>

    <div v-if="fileQuery.isSuccess.value && fileQuery.data.value" class="file-content">
      <pre><code>{{ fileQuery.data.value }}</code></pre>
    </div>

    <div v-else-if="fileQuery.isLoading.value" class="loading">Loading file content...</div>

    <div v-else-if="fileQuery.isError.value" class="error">
      {{ fileQuery.error.value?.message || 'An error occurred loading the file' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'

const route = useRoute()
const router = useRouter()

// Extract the file path from route params
const filePath = computed(() => {
  // The pathMatch will contain the full path after /workflows/
  return (route.params.pathMatch as string[]).join('/')
})

const fileName = computed(() => {
  const parts = filePath.value.split('/')
  return parts[parts.length - 1]
})

const fileQuery = useQuery({
  queryKey: ['fileContent', filePath],
  queryFn: async () => {
    const response = await fetch(`http://localhost:3000/agent-factory/workflows/${filePath.value}`)

    if (!response.ok) {
      throw new Error(`Failed to load file: ${response.statusText}`)
    }

    return response.text()
  },
  // Refetch when the path changes
  enabled: computed(() => !!filePath.value),
})

const goBack = () => {
  router.push('/workflows')
}
</script>

<style scoped>
.file-view {
  width: 100%;
  max-width: 100%;
  text-align: left;
}

.file-nav {
  margin-bottom: 1rem;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  background-color: var(--color-background-soft, #f5f5f5);
  color: var(--color-text, #333);
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-button:hover {
  background-color: var(--color-background-mute, #eaeaea);
  border-color: var(--color-border-hover, #aaa);
}

.back-icon {
  font-size: 1.1rem;
}

.file-header {
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border, #ddd);
}

.file-path {
  color: var(--color-text-light, #888);
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.file-content {
  background: var(--color-background-soft, #f5f5f5);
  border-radius: 6px;
  padding: 1rem;
  overflow-x: auto;
  color: var(--color-text, #333);
  border: 1px solid var(--color-border, #ddd);
}

pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
}

.loading,
.error {
  padding: 1rem;
  background: var(--color-background-soft, #f5f5f5);
  border-radius: 6px;
  color: var(--color-text, #333);
  border: 1px solid var(--color-border, #ddd);
}

.error {
  color: var(--color-error, #d32f2f);
  border-color: var(--color-error-border, #ffcdd2);
}
</style>
