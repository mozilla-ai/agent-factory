import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { workflowService } from '@/services/workflowService'
import type { WorkflowFile } from '@/types'

export const useWorkflowsStore = defineStore('workflows', () => {
  const workflows = ref<WorkflowFile[]>([])
  const loading = ref(false)
  const error = ref('')

  // Fetch workflows
  async function loadWorkflows() {
    try {
      loading.value = true
      error.value = ''
      const data = await workflowService.getWorkflows()
      workflows.value = data
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
