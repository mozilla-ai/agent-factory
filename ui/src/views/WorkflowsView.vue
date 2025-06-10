<template>
  <div>
    <h1>Workflows</h1>

    <ul v-if="workflowsQuery.isLoading.value" class="loading">
      <li>Loading workflows...</li>
    </ul>
    <ul v-else-if="workflowsQuery.isError.value" class="error">
      <li>Error loading workflows: {{ workflowsQuery.error.value?.message }}</li>
    </ul>
    <ul v-else-if="workflowsQuery.data.value?.length === 0" class="no-workflows">
      <li>No workflows found.</li>
    </ul>
    <ul v-else class="workflows-list">
      <li v-for="workflow in workflowsQuery.data.value" :key="workflow.name">
        <FileTree :item="workflow" />
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import FileTree from '../components/FileTree.vue'

export type File = {
  name: string
  isDirectory: boolean
  files?: File[]
}

const workflowsQuery = useQuery<File[]>({
  queryKey: ['workflows'],
  queryFn: async () => {
    const response = await fetch('http://localhost:3000/agent-factory/workflows')
    if (!response.ok) {
      throw new Error('Network response was not ok')
    }
    return response.json()
  },
})
</script>

<style scoped>
.loading,
.error,
.no-workflows {
  color: #666;
  font-style: italic;
}

.workflows-list {
  list-style-type: none;
  padding-left: 0;
  text-align: left;
}
</style>
