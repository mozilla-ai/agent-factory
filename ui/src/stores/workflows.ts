import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type File = {
  name: string
  isDirectory: boolean
  files?: File[]
  path?: string
  content?: string
}

export const useWorkflowsStore = defineStore('workflows', () => {
  const workflows = ref<File[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed getters
  const getWorkflowById = computed(() => {
    return (id: string) => workflows.value.find((w) => w.name === id)
  })

  const latestWorkflow = computed(() => {
    return workflows.value.find((w) => w.name === 'latest')
  })

  const archiveWorkflows = computed(() => {
    return workflows.value.filter((w) => w.name !== 'latest')
  })

  // Actions
  async function loadWorkflows() {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('http://localhost:3000/agent-factory/workflows')

      if (!response.ok) {
        throw new Error(`Failed to fetch workflows: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      workflows.value = processWorkflowsData(data)
    } catch (err) {
      console.error('Error loading workflows:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  // Process raw workflow data into a more usable format
  function processWorkflowsData(data: any[]): File[] {
    const result: File[] = []

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
        // For the archive directory, include each sub-workflow as a top-level item
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

  return {
    workflows,
    loading,
    error,
    getWorkflowById,
    latestWorkflow,
    archiveWorkflows,
    loadWorkflows,
  }
})
