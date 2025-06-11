<template>
  <div class="workflow-details-container">
    <div v-if="loading" class="loading">Loading workflow details...</div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <div v-else-if="workflow" class="workflow-details">
      <div class="workflow-header">
        <h2>{{ workflow.name }}</h2>
        <button class="back-button" @click="goBack">Back to all workflows</button>
      </div>

      <!-- Tabs navigation -->
      <div class="tabs">
        <button
          class="tab-button"
          :class="{ active: activeTab === 'files' }"
          @click="setActiveTab('files')"
        >
          Files
        </button>
        <button
          class="tab-button"
          :class="{ active: activeTab === 'evaluate' }"
          @click="setActiveTab('evaluate')"
        >
          Evaluate
        </button>
        <button
          v-if="hasEvaluationFiles"
          class="tab-button"
          :class="{ active: activeTab === 'results' }"
          @click="setActiveTab('results')"
        >
          Results
        </button>
      </div>

      <!-- Tab content -->
      <div class="tab-content">
        <!-- Files tab with split view -->
        <div v-if="activeTab === 'files'" class="files-tab">
          <div class="file-explorer">
            <!-- File tree on the left -->
            <div class="file-tree-container">
              <h3>Files</h3>
              <div class="file-browser">
                <!-- Custom file tree rendering -->
                <div class="custom-file-tree">
                  <ul class="file-list">
                    <template v-for="file in workflow.files" :key="file.name">
                      <li
                        class="file-item"
                        :class="{
                          'file-item--directory': file.isDirectory,
                          'file-item--selected': selectedFile === file,
                        }"
                        @click="selectFile(file)"
                      >
                        <span class="file-icon">
                          <template v-if="file.isDirectory">📁</template>
                          <template v-else>📄</template>
                        </span>
                        <span class="file-name">{{ file.name }}</span>
                      </li>
                      <!-- Render any nested files if it's a directory and expanded -->
                      <template v-if="file.isDirectory && file === selectedFile && file.files">
                        <li
                          v-for="subFile in file.files"
                          :key="`${file.name}/${subFile.name}`"
                          class="file-item file-item--nested"
                          :class="{
                            'file-item--directory': subFile.isDirectory,
                            'file-item--selected': selectedFile === subFile,
                          }"
                          @click.stop="selectFile(subFile)"
                        >
                          <span class="file-icon">
                            <template v-if="subFile.isDirectory">📁</template>
                            <template v-else>📄</template>
                          </span>
                          <span class="file-name">{{ subFile.name }}</span>
                        </li>
                      </template>
                    </template>
                  </ul>
                </div>
              </div>
            </div>

            <!-- File content on the right -->
            <div class="file-content-container">
              <div v-if="selectedFile && !selectedFile.isDirectory" class="file-content-header">
                <h3>{{ selectedFile.name }}</h3>
                <a
                  :href="`http://localhost:3000/agent-factory/workflows/${workflowPath}/${selectedFile.name}`"
                  target="_blank"
                  class="download-link"
                >
                  Download/View Raw
                </a>
              </div>
              <div v-else-if="selectedFile && selectedFile.isDirectory" class="file-content-header">
                <h3>Directory: {{ selectedFile.name }}</h3>
              </div>
              <div v-else class="file-content-header">
                <h3>Select a file to view its content</h3>
              </div>

              <!-- File content display -->
              <div class="file-content">
                <div v-if="loadingFileContent" class="loading-file">Loading file content...</div>
                <div v-else-if="selectedFile && !selectedFile.isDirectory">
                  <!-- Handle text content -->
                  <pre class="code-preview">{{ fileContent }}</pre>
                </div>
                <div v-else-if="selectedFile && selectedFile.isDirectory" class="directory-info">
                  <p>This is a directory containing {{ selectedFile.files?.length || 0 }} items</p>
                </div>
                <div v-else class="no-file-selected">
                  <p>No file selected. Click on a file in the tree to view its content.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Evaluation tab -->
        <div v-if="activeTab === 'evaluate'" class="evaluate-tab">
          <EvaluationPanel
            :workflow-path="workflowPath"
            :evaluation-status="evaluationStatusQuery.data.value"
            @evaluation-status-changed="handleEvaluationStatusChange"
          />
        </div>

        <!-- Results tab -->
        <div v-if="activeTab === 'results'" class="results-tab">
          <h3>Evaluation Results</h3>

          <div class="eval-files-grid">
            <div class="eval-file-card" v-if="evaluationStatusQuery.data.value?.hasAgentTrace">
              <div class="card-header">
                <h4>Agent Execution Trace</h4>
              </div>
              <div class="card-content">
                <p>Contains the detailed trace of the agent's execution</p>
              </div>
              <div class="card-actions">
                <!-- Use direct file access path -->
                <router-link
                  :to="`/workflows/${workflowPath}/agent_eval_trace.json`"
                  class="view-button"
                >
                  View Trace
                </router-link>
              </div>
            </div>

            <div class="eval-file-card" v-if="evaluationStatusQuery.data.value?.hasEvalCases">
              <div class="card-header">
                <h4>Evaluation Cases</h4>
              </div>
              <div class="card-content">
                <p>Contains evaluation test cases for the agent</p>
              </div>
              <div class="card-actions">
                <router-link
                  :to="`/workflows/${workflowPath}/evaluation_case.yaml`"
                  class="view-button"
                >
                  View Cases
                </router-link>
              </div>
            </div>

            <div class="eval-file-card" v-if="evaluationStatusQuery.data.value?.hasEvalResults">
              <div class="card-header">
                <h4>Evaluation Results</h4>
              </div>
              <div class="card-content">
                <p>Contains the results of running evaluation on this agent</p>
              </div>
              <div class="card-actions">
                <router-link
                  :to="`/workflows/${workflowPath}/evaluation_results.json`"
                  class="view-button"
                >
                  View Results
                </router-link>
              </div>
            </div>
          </div>

          <div v-if="!hasEvaluationFiles" class="no-results">
            <p>No evaluation files found. Run evaluation first to generate results.</p>
            <button class="action-button" @click="setActiveTab('evaluate')">
              Go to Evaluation
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkflowsStore } from '../stores/workflows'
import EvaluationPanel from '../components/EvaluationPanel.vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'

// Define types for file structure
interface File {
  name: string
  isDirectory: boolean
  files?: File[]
}

interface EvaluationStatus {
  hasAgentTrace: boolean
  hasEvalCases: boolean
  hasEvalResults: boolean
}

const route = useRoute()
const router = useRouter()
const workflowsStore = useWorkflowsStore()
const queryClient = useQueryClient()

// UI state with proper types
const loading = ref<boolean>(false)
const error = ref<string>('')
const activeTab = ref<string>('files')
const selectedFile = ref<File | undefined>(undefined) // Changed from null to undefined
const loadingFileContent = ref<boolean>(false)
const fileContent = ref<string>('')

// Extract the workflow id from the route
const workflowId = computed(() => route.params.id as string)

// Get the workflow from store or fetch it
const workflow = computed(() => {
  return workflowsStore.getWorkflowById(workflowId.value)
})

// Computed workflow path for API calls
const workflowPath = computed(() => {
  if (!workflow.value) return ''
  return (
    workflow.value.path ||
    (workflow.value.name === 'latest' ? 'latest' : `archive/${workflow.value.name}`)
  )
})

// Use the current value in the query key
const evaluationStatusQuery = useQuery({
  queryKey: ['evaluationStatus', workflowPath.value],
  queryFn: async (): Promise<EvaluationStatus> => {
    console.log('Fetching evaluation status for:', workflowPath.value)

    if (!workflowPath.value)
      return {
        hasAgentTrace: false,
        hasEvalCases: false,
        hasEvalResults: false,
      }

    // We'll check for existence of each file
    const [hasAgentTrace, hasEvalCases, hasEvalResults] = await Promise.all([
      checkFileExists(`${workflowPath.value}/agent_eval_trace.json`),
      checkFileExists(`${workflowPath.value}/evaluation_case.yaml`),
      checkFileExists(`${workflowPath.value}/evaluation_results.json`),
    ])

    console.log('File check results:', {
      hasAgentTrace,
      hasEvalCases,
      hasEvalResults,
    })

    return {
      hasAgentTrace,
      hasEvalCases,
      hasEvalResults,
    }
  },
  enabled: computed(() => !!workflowPath.value),
})

// Watch for workflow path changes to refetch evaluation status
watch(
  () => workflowPath.value,
  (newPath, oldPath) => {
    console.log('Workflow path changed from:', oldPath, 'to:', newPath)
    if (newPath && newPath !== oldPath) {
      console.log('Refetching evaluation status')
      queryClient.invalidateQueries({
        queryKey: ['evaluationStatus', newPath],
      })
    }
  },
)

// Helper function to check if a file exists
async function checkFileExists(filePath: string): Promise<boolean> {
  try {
    const response = await fetch(`http://localhost:3000/agent-factory/workflows/${filePath}`, {
      method: 'GET',
    })
    return response.ok
  } catch (e) {
    console.error(`Error checking file ${filePath}:`, e)
    return false
  }
}

// The computed property for if any evaluation files exist
const hasEvaluationFiles = computed((): boolean => {
  const status = evaluationStatusQuery.data.value
  if (!status) {
    console.log('No evaluation status data available yet')
    return false
  }
  const result = !!(status.hasAgentTrace || status.hasEvalCases || status.hasEvalResults)

  console.log('hasEvaluationFiles computed:', result)
  return result
})

// Set active tab and update URL
function setActiveTab(tab: string): void {
  activeTab.value = tab
  selectedFile.value = undefined // Changed from null to undefined
  fileContent.value = ''

  // Update URL to preserve tab when refreshing
  router.replace({
    path: route.path,
    query: { tab },
  })
}

// Go back to workflows list
function goBack(): void {
  router.push('/workflows')
}

// Helper to find parent directory of a file
function findParent(files: File[] | undefined, target: File): File | undefined {
  if (!files) return undefined;

  for (const file of files) {
    if (file.isDirectory && file.files) {
      if (file.files.some((f) => f === target)) {
        return file
      }

      const nestedResult = findParent(file.files, target)
      if (nestedResult) {
        return nestedResult
      }
    }
  }
  return undefined // Changed from null to undefined
}

// Select a file and load its content
async function selectFile(file: File): Promise<void> {
  // If it's a directory, don't load content
  if (file.isDirectory) {
    selectedFile.value = file
    return
  }

  // Get the full path to the file
  let filePath = `${workflowPath.value}/${file.name}`

  // If this file is nested in directories, we need to build the full path
  let parent = workflow.value?.files ? findParent(workflow.value.files, file) : undefined
  while (parent) {
    filePath = `${workflowPath.value}/${parent.name}/${file.name}`
    parent = workflow.value?.files ? findParent(workflow.value.files, parent) : undefined
  }

  // Load file content
  try {
    loadingFileContent.value = true
    selectedFile.value = file

    const response = await fetch(`http://localhost:3000/agent-factory/workflows/${filePath}`)

    if (!response.ok) {
      fileContent.value = `Error loading file: ${response.status} ${response.statusText}`
      return
    }

    // Check if it's a binary file - if so, provide a link instead
    const contentType = response.headers.get('content-type')
    if (
      contentType &&
      (contentType.includes('image/') ||
        contentType.includes('audio/') ||
        contentType.includes('video/') ||
        contentType.includes('application/octet-stream'))
    ) {
      fileContent.value = `This file type (${contentType}) cannot be displayed inline.\n\nYou can view/download it at:\n${response.url}`
      return
    }

    // For text files, display the content
    const content = await response.text()
    fileContent.value = content
  } catch (error: any) {
    console.error('Error fetching file:', error)
    fileContent.value = `Error loading file: ${error.message}`
  } finally {
    loadingFileContent.value = false
  }
}

// Update the handleEvaluationStatusChange function
async function handleEvaluationStatusChange(status: Partial<EvaluationStatus> & { tab?: string }): Promise<void> {
  if (!status) return

  console.log('Evaluation status changed:', status)

  await queryClient.invalidateQueries({
    queryKey: ['evaluationStatus', workflowPath.value],
  })

  // Switch to tab if specified
  if (status.tab) {
    activeTab.value = status.tab
  }
}

// Watch to ensure the evaluation status is refreshed when switching back to the evaluate tab
watch(
  () => activeTab.value,
  (newTab) => {
    if (newTab === 'evaluate') {
      // Force refetch when switching to evaluate tab to ensure we have up-to-date status
      evaluationStatusQuery.refetch()
    }
  },
)

// Load data when the component is mounted
onMounted(async () => {
  // Load the workflow if not already in store
  if (!workflow.value) {
    loading.value = true
    try {
      await workflowsStore.loadWorkflows()
      if (!workflow.value) {
        error.value = `Workflow "${workflowId.value}" not found`
      }
    } catch (err: any) {
      error.value = `Error loading workflow: ${err.message}`
    } finally {
      loading.value = false
    }
  }

  // Set tab from query parameter if present
  if (route.query.tab) {
    activeTab.value = route.query.tab.toString()
  }
})

// Update the watch to monitor evaluation status changes
watch(
  () => evaluationStatusQuery.data.value,
  (newStatus) => {
    console.log('Evaluation status updated in WorkflowDetailsView:', newStatus)
  },
  { deep: true },
)
</script>

<style scoped>
.workflow-details-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.loading,
.error {
  display: flex;
  padding: 2rem;
  justify-content: center;
  align-items: center;
  color: var(--color-text-light);
  font-style: italic;
}

.error {
  color: var(--color-error, red);
}

.workflow-details {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-button {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.3s;
}

.back-button:hover {
  background: var(--color-background-mute);
  border-color: var(--color-border-hover);
}

.tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
}

.tab-button {
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
  margin-bottom: -1px;
}

.tab-button:hover {
  color: var(--color-primary);
}

.tab-button.active {
  color: var(--color-primary);
  border-bottom: 2px solid var(--color-primary);
}

.tab-content {
  display: flex;
  flex-direction: column;
  padding: 1.5rem 0;
}

.file-explorer {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1rem;
  height: 60vh;
}

.file-tree-container,
.file-content-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-background-soft);
}

.file-tree-container h3,
.file-content-header h3 {
  margin: 0;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-mute);
}

.file-content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.download-link {
  margin-right: 1rem;
  font-size: 0.9rem;
  color: var(--color-primary);
  text-decoration: none;
}

.download-link:hover {
  text-decoration: underline;
}

.file-browser {
  flex: 1;
  overflow: auto;
  padding: 0.5rem;
}

.file-content {
  flex: 1;
  overflow: auto;
  padding: 1rem;
}

/* Custom file tree styles */
.custom-file-tree {
  font-family: monospace;
}

.file-list {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.file-item {
  padding: 0.4rem 0.6rem;
  margin: 0.1rem 0;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.file-item:hover {
  background: var(--color-background);
}

.file-item--selected {
  background: var(--color-background-mute) !important;
}

.file-item--directory {
  font-weight: bold;
}

.file-item--nested {
  padding-left: 1.5rem;
}

.file-icon {
  margin-right: 0.5rem;
}

.file-name {
  word-break: break-all;
}

/* File content styles */
.code-preview {
  font-family: monospace;
  white-space: pre-wrap;
  padding: 0;
  margin: 0;
}

.loading-file,
.no-file-selected,
.directory-info {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-light);
}

/* Results tab styles */
.eval-files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.eval-file-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  height: 100%;
}

.card-header {
  display: flex;
  padding: 1rem;
  background: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
}

.card-header h4 {
  margin: 0;
}

.card-content {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  flex: 1;
}

.card-actions {
  display: flex;
  padding: 1rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-background-soft);
}

.view-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  text-decoration: none;
  transition: all 0.3s;
}

.view-button:hover {
  background: var(--color-background-mute);
  border-color: var(--color-border-hover);
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  background: var(--color-primary);
  border: 1px solid var(--color-primary);
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.action-button:hover {
  background: var(--color-primary-dark);
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  text-align: center;
  color: var(--color-text-light);
}

/* Media query for small screens */
@media (max-width: 768px) {
  .file-explorer {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
}
</style>
