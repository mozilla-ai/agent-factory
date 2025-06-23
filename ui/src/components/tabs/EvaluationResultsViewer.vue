<template>
  <div class="results-viewer">
    <StatusMessage
      v-if="statusQuery.isLoading.value || resultsQuery.isLoading.value"
      variant="loading"
      message="Loading evaluation results..."
    />

    <StatusMessage
      v-else-if="statusQuery.isError.value || resultsQuery.isError.value"
      variant="error"
      :message="
        statusQuery.error.value?.message ||
        resultsQuery.error.value?.message ||
        'An error occurred loading evaluation results'
      "
    />

    <div v-else class="results-content">
      <!-- Summary stats if results available -->
      <div v-if="hasValidScoreData" class="results-summary">
        <ScoreCard
          title="Final Score"
          description="Based on point values assigned to each checkpoint"
          :score="scoreValue"
          :max-score="maxScoreValue"
          color-threshold="auto"
        >
          <template #actions>
            <BaseButton variant="danger" @click="handleDeleteClick">Delete Results</BaseButton>
          </template>
        </ScoreCard>
      </div>

      <!-- Evaluation files grid -->
      <div class="eval-files-grid">
        <!-- Agent trace card -->
        <EvaluationCard
          v-if="hasAgentTrace"
          title="Agent Trace"
          description="Contains detailed logs of the agent's execution, including LLM calls, tool usage, and the final output."
          action-label="View Agent Trace"
          :show-actions="true"
          @action="viewAgentTrace"
        />

        <!-- Evaluation criteria card -->
        <EvaluationCard
          v-if="hasEvalCases"
          title="Evaluation Criteria"
          description="The test cases used to evaluate the agent's performance, including criteria, point values, and expected behaviors."
          action-label="View Evaluation Criteria"
          :show-actions="true"
          @action="viewCriteria"
        />

        <!-- Evaluation results card -->
        <EvaluationCard
          v-if="hasEvaluationResults"
          title="Evaluation Results"
          description="The agent's scored performance against each evaluation criterion, with pass/fail status and detailed feedback."
          action-label="View Detailed Results"
          :show-actions="true"
          @action="viewResults"
        >
          <div class="checkpoint-summary">
            <MetricDisplay
              variant="metric"
              label="Total Checkpoints"
              :value="resultsQuery.data.value?.checkpoints.length || 0"
            />

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

            <ProgressBar
              :percentage="scorePercentage"
              :label="`${Math.round(scorePercentage)}% Pass Rate`"
              :show-label="true"
              color-threshold="auto"
            />
          </div>
        </EvaluationCard>
      </div>

      <!-- No results message -->
      <StatusMessage
        v-if="!hasAgentTrace && !hasEvalCases && !hasEvaluationResults"
        variant="empty"
        icon="📊"
        title="No evaluation data available"
        message="Run the agent and generate evaluation cases to see results here."
      >
        <template #actions>
          <BaseButton variant="primary" @click="goToEvaluateTab">Go to Evaluate</BaseButton>
        </template>
      </StatusMessage>
    </div>

    <ConfirmationDialog
      :isOpen="showDeleteDialog"
      :title="deleteOptions.title"
      :message="deleteOptions.message"
      :confirmButtonText="deleteOptions.confirmButtonText"
      :isDangerous="deleteOptions.isDangerous"
      :isLoading="deleteResultsMutation.isPending.value"
      @confirm="confirmDelete"
      @cancel="closeDeleteDialog"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { workflowService } from '@/services/workflowService'
import { evaluationService } from '../../services/evaluationService'
import { useRouter } from 'vue-router'
import ConfirmationDialog from '../ConfirmationDialog.vue'

import { transformResults } from '@/helpers/transform-results'
import { useWorkflowsStore } from '@/stores/workflows'
import { useDeleteConfirmation } from '@/composables/useDeleteConfirmation'
import { useEvaluationScores } from '@/composables/useEvaluationScores'
import StatusMessage from '../StatusMessage.vue'
import ScoreCard from '../ScoreCard.vue'
import EvaluationCard from '../EvaluationCard.vue'
import ProgressBar from '../ProgressBar.vue'
import MetricDisplay from '../MetricDisplay.vue'
import BaseButton from '../BaseButton.vue'

// Props
const props = defineProps<{
  workflowId: string
}>()

const workflowsStore = useWorkflowsStore()
// Setup
const router = useRouter()

// Fetch evaluation status using workflowService
const statusQuery = useQuery({
  queryKey: ['evaluation-status', props.workflowId],
  queryFn: () => workflowService.getEvaluationStatus(props.workflowId),
  retry: 1,
})

// Fetch evaluation results using API client instead of direct fetch
const resultsQuery = useQuery({
  queryKey: ['evaluation-results', props.workflowId],
  queryFn: async () => {
    const data = await evaluationService.getEvaluationResults(props.workflowId)
    // Handle case where data might already be parsed or is an object
    const parsedData = typeof data === 'string' ? JSON.parse(data) : data
    return transformResults(parsedData)
  },
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

// Use evaluation scores composable for consistent calculations
const { passedCheckpoints, failedCheckpoints, scorePercentage } = useEvaluationScores(
  computed(() => undefined), // No criteria needed for results viewer
  resultsQuery.data,
)

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

// Use delete confirmation composable
const { showDeleteDialog, deleteOptions, openDeleteDialog, closeDeleteDialog } =
  useDeleteConfirmation()
const queryClient = useQueryClient()

const deleteResultsMutation = useMutation({
  mutationFn: () => evaluationService.deleteEvaluationResults(props.workflowId),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['evaluation-results', props.workflowId] })
    queryClient.invalidateQueries({ queryKey: ['evaluation-status', props.workflowId] })
    queryClient.invalidateQueries({
      queryKey: ['file-content', props.workflowId, 'evaluation_results.json'],
    })
    closeDeleteDialog()
    // Refresh the workflow store to update file explorer
    workflowsStore.loadWorkflows()
    router.push({
      params: { workflowId: props.workflowId },
      query: { tab: 'evaluate' },
    })
  },
})

function handleDeleteClick() {
  openDeleteDialog({
    title: 'Delete Evaluation Results',
    message:
      'Are you sure you want to delete these evaluation results? This action cannot be undone.',
    confirmButtonText: 'Delete',
  })
}

function confirmDelete() {
  deleteResultsMutation.mutate()
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
</style>
