<template>
  <div class="workflow-details-container">
    <div v-if="loading" class="loading">Loading workflow details...</div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <div v-else-if="workflow" class="workflow-details">
      <div class="workflow-header">
        <h2>{{ workflow.name }}</h2>
        <button class="back-button" @click="navigateBack">Back to all workflows</button>
      </div>

      <!-- Tabs navigation -->
      <div class="tabs">
        <button
          v-for="tab in availableTabs"
          :key="tab.id"
          class="tab-button"
          :class="{ active: activeTab === tab.id }"
          @click="handleTabClicked(tab.id)"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab content -->
      <div class="tab-content">
        <component :is="currentTabComponent" v-bind="tabProps"></component>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkflows } from '@/composables/useWorkflows'
import { useQuery } from '@tanstack/vue-query'
import { useTabs } from '@/composables/useTabs'
import { queryKeys } from '@/helpers/queryKeys'
import { workflowService } from '@/services/workflowService'

// Components
import AgentFileExplorer from '@/components/tabs/AgentFileExplorer.vue'
import AgentEvaluationPanel from '@/components/tabs/AgentEvaluationPanel.vue'
import AgentEvalTraceViewer from '@/components/tabs/AgentEvalTraceViewer.vue'
import EvaluationCriteriaViewer from '@/components/tabs/EvaluationCriteriaViewer.vue'
import EvaluationResultsViewer from '@/components/tabs/EvaluationResultsViewer.vue'
import AgentGenerationTraceViewer from '@/components/tabs/AgentGenerationTraceViewer.vue'
import type { WorkflowFile } from '@/types'

const route = useRoute()
const router = useRouter()
const {
  workflows,
  loading: workflowsLoading,
  error: workflowsError,
  getWorkflowById,
} = useWorkflows()

// Extract the workflow id from the route
const workflowId = computed(() => route.params.id as string)

// Get the workflow from store
const workflow = computed(() => getWorkflowById(workflowId.value))

// Combined loading state: loading if workflows are loading
const loading = computed(() => workflowsLoading.value)

// Combined error state: error if workflows failed to load or workflow not found
const error = computed(() => {
  if (workflowsError.value) return workflowsError.value
  if (!workflowsLoading.value && workflows.value.length > 0 && !workflow.value) {
    return `Workflow "${workflowId.value}" not found`
  }
  return ''
})

const evaluationStatusQuery = useQuery({
  queryKey: computed(() => queryKeys.evaluationStatus(workflowId.value)),
  queryFn: () => workflowService.getEvaluationStatus(workflowId.value),
  enabled: computed(() => !!workflowId.value),
  retry: 1,
})

const { activeTab, setActiveTab } = useTabs('files')

const handleTabClicked = (tab: string) => {
  selectedFile.value = undefined // Reset selected file when changing tabs
  setActiveTab(tab)
}

const selectedFile = ref<WorkflowFile | undefined>(undefined)

// Computed property for selected file path
const selectedFilePath = computed(() =>
  selectedFile.value ? selectedFile.value.path || selectedFile.value.name : null,
)

// Configure file content query with caching
const fileContentQuery = useQuery({
  queryKey: computed(() => queryKeys.fileContent(workflowId.value, selectedFilePath.value || '')),
  queryFn: () => {
    // Make sure we have both required parameters as strings
    if (!workflowId.value || !selectedFilePath.value) {
      return Promise.resolve('') // Return empty string if path is missing
    }
    return workflowService.getFileContent(workflowId.value, selectedFilePath.value)
  },
  enabled: computed(() => !!workflowId.value && !!selectedFilePath.value),
  retry: 1,
})

// Handle file selection
function handleFileSelect(file: WorkflowFile) {
  selectedFile.value = file
}

// Dynamic tab list based on evaluation status
const availableTabs = computed(() => {
  const tabs = [
    { id: 'files', label: 'Files' },
    { id: 'evaluate', label: 'Run Evaluation' },
    { id: 'agent-generation-trace', label: 'Agent Generation Trace' },
  ]

  if (evaluationStatusQuery.data.value?.hasAgentTrace) {
    tabs.push({ id: 'agent-trace', label: 'Agent Trace' })
  }

  tabs.push({ id: 'criteria', label: 'Evaluation Criteria' })

  if (evaluationStatusQuery.data.value?.hasEvalResults) {
    tabs.push({ id: 'results', label: 'Evaluation Results' })
  }

  return tabs
})

// Dynamic component loading based on active tab
const currentTabComponent = computed(() => {
  switch (activeTab.value) {
    case 'files':
      return AgentFileExplorer
    case 'evaluate':
      return AgentEvaluationPanel
    case 'agent-trace':
      return AgentEvalTraceViewer
    case 'criteria':
      return EvaluationCriteriaViewer
    case 'results':
      return EvaluationResultsViewer
    case 'agent-generation-trace':
      return AgentGenerationTraceViewer
    default:
      return AgentFileExplorer
  }
})

// Props to pass to the current tab component
const tabProps = computed(() => {
  const baseProps = {
    workflowId: workflowId.value,
  }

  // Add tab-specific props
  switch (activeTab.value) {
    case 'files':
      return {
        ...baseProps,
        files: workflow.value?.files || [],
        selectedFile: selectedFile.value,
        content:
          typeof fileContentQuery.data.value === 'string'
            ? fileContentQuery.data.value
            : JSON.stringify(fileContentQuery.data.value, null, 2) || '',
        loading: fileContentQuery.isLoading.value,
        error: fileContentQuery.error.value?.message || '',
        onSelect: handleFileSelect,
      }
    case 'evaluate':
      return {
        ...baseProps,
        evaluationStatus: evaluationStatusQuery.data.value,
        onEvaluationStatusChanged: handleEvaluationStatusChange,
      }
    default:
      return baseProps
  }
})

// Handle evaluation status changes
function handleEvaluationStatusChange() {
  // Invalidate the query to refresh evaluation status
  evaluationStatusQuery.refetch()
}

// Navigation
function navigateBack() {
  router.push('/workflows')
}

// Set tab from query parameter when component mounts
onMounted(() => {
  if (route.query.tab) {
    setActiveTab(route.query.tab.toString())
  }
})
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
  border-radius: 0;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
  margin-bottom: -1px;
}

.tab-button:hover {
  color: var(--link-color);
}

.tab-button.active {
  color: var(--link-color);
  border-bottom: 2px solid var(--link-color);
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
  color: var(--link-color);
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
  background: var(--button-background-color);
  border: 1px solid var(--button-background-color);
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.action-button:hover {
  background: var(--button-hover-color);
}

.action-button:active {
  background: var(--button-active-color);
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
