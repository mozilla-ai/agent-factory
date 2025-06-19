<template>
  <div class="results-viewer">
    <div v-if="statusQuery.isLoading.value || resultsQuery.isLoading.value" class="loading-results">
      Loading evaluation results...
    </div>
    <div v-else-if="statusQuery.isError.value || resultsQuery.isError.value" class="error-results">
      {{ statusQuery.error.value || resultsQuery.error.value }}
    </div>
    <div v-else class="results-content">
      <!-- Summary stats if results available -->
      <div v-if="hasValidScoreData" class="results-summary">
        <div class="score-card">
          <div class="score-header">
            <div style="display: flex; justify-content: space-between; align-items: center">
              Final Score
              <button class="delete-button" @click="openDeleteDialog">Delete Results</button>
            </div>
            <div class="score-description">Based on point values assigned to each checkpoint</div>
          </div>
          <div class="score-value">{{ scoreValue }} / {{ maxScoreValue }}</div>
          <div class="score-percentage">{{ scorePercentage }}%</div>
          <div class="score-bar">
            <div
              class="score-progress"
              :style="{ width: `${scorePercentageRaw}%` }"
              :class="scoreColorClass"
            ></div>
          </div>
        </div>
      </div>

      <!-- Evaluation files grid -->
      <div class="eval-files-grid">
        <!-- Agent trace card -->
        <div v-if="hasAgentTrace" class="eval-file-card">
          <div class="card-header">
            <h4>Agent Trace</h4>
          </div>
          <div class="card-content">
            <p>
              Contains detailed logs of the agent's execution, including LLM calls, tool usage, and
              the final output.
            </p>
          </div>
          <div class="card-actions">
            <!-- Replace tab navigation with direct file links -->
            <button class="view-button" @click="viewAgentTrace">View Agent Trace</button>
          </div>
        </div>

        <!-- Evaluation criteria card -->
        <div v-if="hasEvalCases" class="eval-file-card">
          <div class="card-header">
            <h4>Evaluation Criteria</h4>
          </div>
          <div class="card-content">
            <p>
              The test cases used to evaluate the agent's performance, including criteria, point
              values, and expected behaviors.
            </p>
          </div>
          <div class="card-actions">
            <button class="view-button" @click="viewCriteria">View Evaluation Criteria</button>
          </div>
        </div>

        <!-- Evaluation results card -->
        <div v-if="hasEvaluationResults" class="eval-file-card">
          <div class="card-header">
            <h4>Evaluation Results</h4>
          </div>
          <div class="card-content">
            <p>
              The agent's scored performance against each evaluation criterion, with pass/fail
              status and detailed feedback.
            </p>

            <div class="checkpoint-summary">
              <div class="checkpoint-stat">
                <div class="stat-label">Total Checkpoints</div>
                <div class="stat-value">{{ resultsQuery.data.value.checkpoints.length }}</div>
              </div>

              <div class="checkpoint-results">
                <div class="checkpoint-result passed">
                  <div class="result-indicator"></div>
                  <div class="result-details">
                    <div class="result-count">{{ passedCheckpoints }}</div>
                    <div class="result-label">Passed</div>
                  </div>
                </div>

                <div class="checkpoint-result failed">
                  <div class="result-indicator"></div>
                  <div class="result-details">
                    <div class="result-count">{{ failedCheckpoints }}</div>
                    <div class="result-label">Failed</div>
                  </div>
                </div>
              </div>

              <div class="checkpoint-progress">
                <div class="progress-bar">
                  <div
                    class="progress-value"
                    :style="{
                      width: `${(passedCheckpoints / (resultsQuery.data.value.checkpoints.length || 1)) * 100}%`,
                    }"
                  ></div>
                </div>
                <div class="progress-label">
                  {{
                    Math.round(
                      (passedCheckpoints / (resultsQuery.data.value.checkpoints.length || 1)) * 100,
                    )
                  }}% Pass Rate
                </div>
              </div>
            </div>
          </div>
          <div class="card-actions">
            <button class="view-button" @click="viewResults">View Detailed Results</button>
          </div>
        </div>
      </div>

      <!-- No results message -->
      <div v-if="!hasAgentTrace && !hasEvalCases && !hasEvaluationResults" class="no-results">
        <div class="no-results-icon">📊</div>
        <h3>No evaluation data available</h3>
        <p>Run the agent and generate evaluation cases to see results here.</p>
        <button class="action-button" @click="goToEvaluateTab">Go to Evaluate</button>
      </div>
    </div>

    <ConfirmationDialog
      :isOpen="showDeleteDialog"
      title="Delete Evaluation Results"
      message="Are you sure you want to delete these evaluation results? This action cannot be undone."
      confirmButtonText="Delete"
      :isDangerous="true"
      :isLoading="deleteResultsMutation.isPending.value"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { workflowService } from '@/services/workflowService'
import { deleteEvaluationResults } from '../../services/evaluationService'
import { useRouter } from 'vue-router'
import ConfirmationDialog from '../ConfirmationDialog.vue'
import type { EvaluationCheckpoint } from '@/types'
import { useWorkflowsStore } from '@/stores/workflows'

// Props
const props = defineProps<{
  workflowPath: string
}>()

const workflowsStore = useWorkflowsStore()
// Setup
const router = useRouter()

// Fetch evaluation status using workflowService
const statusQuery = useQuery({
  queryKey: ['evaluation-status', props.workflowPath],
  queryFn: () => workflowService.getEvaluationStatus(props.workflowPath),
  retry: 1,
})

// Fetch evaluation results using API client instead of direct fetch
const resultsQuery = useQuery({
  queryKey: ['evaluation-results', props.workflowPath],
  queryFn: () => workflowService.getEvaluationResults(props.workflowPath),
  retry: 1,
})

// Computed properties for evaluation files
const hasAgentTrace = computed(() => statusQuery.data.value?.hasAgentTrace)
const hasEvalCases = computed(() => statusQuery.data.value?.hasEvalCases)
const hasEvaluationResults = computed(() => statusQuery.data.value?.hasEvalResults)

// Safety checks for score data
const hasValidScoreData = computed(() => {
  return (
    resultsQuery.data.value &&
    typeof resultsQuery.data.value.score === 'number' &&
    typeof resultsQuery.data.value.maxScore === 'number' &&
    resultsQuery.data.value.maxScore > 0
  )
})

// Convert normalized score to raw points if needed
const scoreValue = computed(() => {
  if (!resultsQuery.data.value) return 0

  const score = resultsQuery.data.value.score
  const maxScore = resultsQuery.data.value.maxScore || 1

  // Check if score is likely a normalized value (between 0 and 1)
  if (score >= 0 && score <= 1) {
    // Convert from normalized value to raw points
    return Math.round(score * maxScore)
  }

  // Already in raw points
  return score
})

const maxScoreValue = computed(() => resultsQuery.data.value?.maxScore ?? 1)

// Calculate percentage correctly
const scorePercentageRaw = computed(() => {
  if (!hasValidScoreData.value) return 0

  // Use normalized score if available, otherwise calculate percentage
  if (resultsQuery.data.value.score >= 0 && resultsQuery.data.value.score <= 1) {
    return resultsQuery.data.value.score * 100
  }

  return (scoreValue.value / maxScoreValue.value) * 100
})

// Format to whole number percentage
const scorePercentage = computed(() => Math.round(scorePercentageRaw.value))

// Score color based on percentage
const scoreColorClass = computed(() => {
  if (scorePercentage.value >= 80) return 'score-excellent'
  if (scorePercentage.value >= 50) return 'score-good'
  return 'score-poor'
})

// Add the missing computed properties for checkpoint counts
const passedCheckpoints = computed(() => {
  if (!resultsQuery.data.value?.checkpoints) return 0
  return resultsQuery.data.value.checkpoints.filter(
    (c: EvaluationCheckpoint) => c.result === 'pass',
  ).length
})

const failedCheckpoints = computed(() => {
  if (!resultsQuery.data.value?.checkpoints) return 0
  return resultsQuery.data.value.checkpoints.filter(
    (c: EvaluationCheckpoint) => c.result === 'fail',
  ).length
})

// Navigation methods
// function viewFile(filename: string) {
//   const basePath = props.workflowPath === 'latest' ? 'latest' : `archive/${props.workflowPath}`

//   router.push(`/workflows/${basePath}/${filename}`)
// }

function viewAgentTrace() {
  router.push({
    path: router.currentRoute.value.path,
    query: { ...router.currentRoute.value.query, tab: 'agent-trace' },
  })
}

function viewCriteria() {
  router.push({
    path: router.currentRoute.value.path,
    query: { ...router.currentRoute.value.query, tab: 'criteria' },
  })
}

function viewResults() {
  // Navigate to the criteria tab to show detailed results
  router.push({
    path: router.currentRoute.value.path,
    query: { ...router.currentRoute.value.query, tab: 'criteria' },
  })
}

function goToEvaluateTab() {
  router.push({
    path: router.currentRoute.value.path,
    query: { ...router.currentRoute.value.query, tab: 'evaluate' },
  })
}

// Add these new lines for delete functionality
const showDeleteDialog = ref(false)
const queryClient = useQueryClient()

const deleteResultsMutation = useMutation({
  mutationFn: () => deleteEvaluationResults(props.workflowPath),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['evaluation-results', props.workflowPath] })
    queryClient.invalidateQueries({ queryKey: ['evaluation-status', props.workflowPath] })
    queryClient.invalidateQueries({
      queryKey: ['file-content', props.workflowPath, 'evaluation_results.json'],
    })
    showDeleteDialog.value = false
    // Refresh the workflow store to update file explorer
    workflowsStore.loadWorkflows()
    router.push({
      params: { workflowPath: props.workflowPath },
      query: { tab: 'evaluate' },
    })
  },
})

const openDeleteDialog = () => {
  showDeleteDialog.value = true
}

const confirmDelete = () => {
  deleteResultsMutation.mutate()
}

const cancelDelete = () => {
  showDeleteDialog.value = false
}
</script>

<style scoped>
.results-viewer {
  padding: 1rem;
}

.loading-results,
.error-results {
  text-align: center;
  padding: 2rem;
  font-size: 1.125rem;
}

.error-results {
  color: var(--color-error, #f56c6c);
}

.results-summary {
  margin-bottom: 1.5rem;
}

.score-card {
  background: var(--color-background-soft);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--color-border);
}

.score-header {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.score-description {
  font-size: 0.75rem;
  font-weight: normal;
  color: var(--color-text-light);
  margin-top: 0.25rem;
}

.score-value {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
}

.score-percentage {
  font-size: 0.875rem;
  color: var(--color-text-light);
}

.score-bar {
  background: var(--color-background-mute);
  border-radius: 4px;
  height: 8px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.score-progress {
  height: 100%;
  transition: width 0.5s ease;
}

.results-content {
  display: flex;
  flex-direction: column;
}

.eval-files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.eval-file-card {
  background: var(--color-background-soft);
  border-radius: 8px;
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card-header {
  font-size: 1.125rem;
  font-weight: 500;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-mute);
}

.card-header h4 {
  margin: 0;
}

.card-content {
  font-size: 0.875rem;
  color: var(--color-text);
  padding: 1rem;
  flex: 1;
}

.card-actions {
  padding: 1rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-background-mute);
}

.view-button {
  background: var(--button-background-color);
  color: white; /* Most button text on colored backgrounds is white */
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  width: 100%;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.view-button:hover {
  background: var(--button-hover-color);
}

.view-button:active {
  background: var(--button-active-color);
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: var(--color-text-light);
}

.no-results-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.action-button {
  background: var(--button-background-color);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.625rem 1.25rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.action-button:hover {
  background: var(--button-hover-color);
}

.action-button:active {
  background: var(--button-active-color);
}

/* Score color classes that maintain theme compatibility */
.score-excellent {
  background: var(--color-success, #4caf50);
}

.score-good {
  background: var(--color-warning, #ff9800);
}

.score-poor {
  background: var(--color-error, #f44336);
}

.checkpoint-summary {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.checkpoint-stat {
  background: var(--color-background-mute);
  padding: 0.75rem;
  border-radius: 6px;
  text-align: center;
}

.stat-label {
  font-size: 0.8rem;
  color: var(--color-text-light);
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
}

.checkpoint-results {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.checkpoint-result {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border-radius: 6px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
}

.checkpoint-result.passed {
  border-left: 4px solid var(--color-success, #4caf50);
}

.checkpoint-result.failed {
  border-left: 4px solid var(--color-error, #f44336);
}

.result-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 0.75rem;
}

.passed .result-indicator {
  background-color: var(--color-success, #4caf50);
}

.failed .result-indicator {
  background-color: var(--color-error, #f44336);
}

.result-details {
  display: flex;
  flex-direction: column;
}

.result-count {
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1;
}

.result-label {
  font-size: 0.8rem;
  color: var(--color-text-light);
}

.checkpoint-progress {
  margin-top: 0.5rem;
}

.progress-bar {
  height: 6px;
  background: var(--color-background-mute);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.25rem;
}

.progress-value {
  height: 100%;
  background: var(--color-success, #4caf50);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-label {
  font-size: 0.75rem;
  color: var(--color-text-light);
  text-align: right;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.delete-button {
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  border: 1px solid var(--color-error);
  background-color: var(--color-error-soft);
  color: var(--color-error);
  font-weight: 500;
  cursor: pointer;
}

.delete-button:hover {
  background-color: var(--color-error);
  color: white;
}
</style>
