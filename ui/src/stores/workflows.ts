import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { workflowService } from '@/services/workflowService'
import type { Workflow, File } from '@/types'

export const useWorkflowsStore = defineStore('workflows', () => {
  const workflows = ref<Workflow[]>([])
  const loading = ref(false)
  const error = ref('')

  // Process raw workflow data
  function processWorkflowsData(data: File[]): Workflow[] {
    const result: Workflow[] = []

    for (const item of data) {
      if (item.name === 'latest') {
        // Add latest directly with proper path
        result.push({
          name: 'latest',
          isDirectory: true,
          files: item.files || [],
          path: 'latest',
        })
      } else if (item.name === 'archive' && item.isDirectory && item.files) {
        // For archive directory, include each sub-workflow as a top-level item
        for (const archiveWorkflow of item.files) {
          if (archiveWorkflow.isDirectory) {
            result.push({
              name: archiveWorkflow.name,
              isDirectory: true,
              files: archiveWorkflow.files || [],
              path: `archive/${archiveWorkflow.name}`,
            })
          }
        }
      }
    }

    return result
  }

  // Fetch workflows
  async function loadWorkflows() {
    try {
      loading.value = true
      error.value = ''
      const data = await workflowService.getWorkflows()
      workflows.value = processWorkflowsData(data)
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err)
      console.error('Error loading workflows:', err)
    } finally {
      loading.value = false
    }
  }

  // Get workflow by ID
  const getWorkflowById = computed(() => (id: string) => {
    return workflows.value.find((w) => w.name === id || w.path === id)
  })

  return {
    workflows,
    loading,
    error,
    loadWorkflows,
    getWorkflowById,
  }
})
