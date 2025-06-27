<template>
  <div class="file-view">
    <!-- Only show back button when used as a standalone page -->
    <div v-if="!workflowId" class="file-nav">
      <button class="back-button" @click="goBack"><span class="back-icon">←</span> Back</button>
    </div>

    <!-- Show close button when embedded in another view -->
    <div v-else class="file-nav file-nav-embedded">
      <h3>{{ fileName }}</h3>
      <button class="close-button" @click="$emit('close')"><span>✕</span> Close</button>
    </div>

    <div class="file-header">
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
import { workflowService } from '@/services/workflowService'
import { queryKeys } from '@/helpers/queryKeys'

const props = defineProps({
  // When used as an embedded component
  pathMatch: {
    type: Array,
    default: () => [],
  },
  workflowId: {
    type: String,
    default: '',
  },
})

defineEmits(['close'])

const route = useRoute()
const router = useRouter()

// Extract the file path from route params or props
const filePath = computed(() => {
  // If we have pathMatch prop, use that (embedded mode)
  if (props.pathMatch && props.pathMatch.length > 0) {
    return props.pathMatch.join('/')
  }

  // Otherwise use the route params (standalone mode)
  return (route.params.pathMatch as string[])?.join('/') || ''
})

const fileName = computed(() => {
  const parts = filePath.value.split('/')
  return parts[parts.length - 1]
})

const fileQuery = useQuery({
  queryKey: computed(() => queryKeys.fileContent(props.workflowId, filePath.value)),
  queryFn: async () => {
    try {
      const data = await workflowService.getFileContent(route.params.id as string, filePath.value)
      return data
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      throw new Error(`Failed to load file: ${errorMessage}`)
    }
  },
  enabled: computed(() => !!filePath.value),
  retry: 1,
})

// Navigation function - only used in standalone mode
const goBack = () => {
  // If we have a workflowId, go back to that workflow
  router.back()
}
</script>

<style scoped>
.file-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  text-align: left;
}

.file-nav {
  padding: 0.75rem 1rem;
  /* background-color: var(--color-background-soft); */
  border-bottom: 1px solid var(--color-border);
}

.file-nav-embedded {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-nav-embedded h3 {
  margin: 0;
  font-size: 1rem;
}

.back-button,
.close-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  background-color: var(--color-background);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-button:hover,
.close-button:hover {
  background-color: var(--color-background-mute);
  border-color: var(--color-border-hover);
}

.back-icon {
  font-size: 1.1rem;
}

.file-header {
  padding: 0.5rem 1rem;
  background-color: var(--color-background);
}

.file-path {
  color: var(--color-text-light);
  font-size: 0.9rem;
  font-family: monospace;
}

.file-content {
  flex: 1;
  overflow: auto;
  background: var(--color-background-soft);
  padding: 1rem;
  color: var(--color-text);
}

pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
}

.loading,
.error {
  flex: 1;
  padding: 1rem;
  background: var(--color-background-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text);
}

.error {
  color: var(--color-error, #d32f2f);
}
</style>
