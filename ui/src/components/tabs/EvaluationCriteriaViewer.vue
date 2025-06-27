<template>
  <div class="evaluation-criteria-viewer">
    <!-- Loading state -->
    <div v-if="evaluationCriteriaQuery.isPending.value" class="criteria-loading">
      Loading evaluation criteria...
    </div>

    <!-- Error state for missing criteria file -->
    <div v-else-if="hasCriteriaError && !isEditMode" class="empty-criteria-container">
      <div class="empty-criteria-message">
        <h3>No Evaluation Criteria Found</h3>
        <p>
          This workflow doesn't have any evaluation criteria defined yet. Evaluation criteria help
          you assess the performance of your agent against specific goals.
        </p>
      </div>
      <BaseButton variant="primary" @click="startCreatingCriteria">
        Create Evaluation Criteria
      </BaseButton>
    </div>

    <!-- Form for creating/editing -->
    <div
      v-else-if="!evaluationCriteriaQuery.data.value || isEditMode"
      class="criteria-form-container"
    >
      <EvaluationCriteriaForm
        :workflowId="workflowId"
        :initialData="isEditMode ? evaluationCriteriaQuery.data.value : null"
        @saved="onCriteriaSaved"
        @cancel="isEditMode = false"
      />
    </div>

    <!-- Show existing criteria -->
    <div v-else class="criteria-content">
      <!-- Header with judge info -->
      <div class="criteria-header">
        <div class="header-content">
          <h3>Evaluation Criteria</h3>
          <div class="judge-info">
            <span class="judge-label">LLM Judge:</span>
            <span class="judge-model">{{ evaluationCriteriaQuery.data.value.llm_judge || 'N/A (auto-generated)' }}</span>
          </div>
          <!-- Scoring functionality preserved for future use when Python code adds scoring support -->
          <div class="points-summary">
            <span class="points-label">Total Points Possible:</span>
            <span class="points-value">{{ totalPossiblePoints }}</span>
          </div>
        </div>

        <div class="header-actions">
          <BaseButton variant="secondary" @click="toggleEditMode">Edit Criteria</BaseButton>
          <BaseButton variant="danger" @click="handleDeleteClick">Delete</BaseButton>
        </div>
      </div>

      <!-- Final score (if results available) -->
      <div v-if="hasResults" class="final-score">
        <h3>Final Score</h3>
        <div class="score-display">
          <div class="score-value">{{ totalScore }} / {{ totalPossiblePoints }}</div>
          <div class="score-percentage">{{ Math.round(scorePercentage) }}%</div>
        </div>
        <div class="score-bar">
          <div
            class="score-progress"
            :style="{ width: `${scorePercentage}%` }"
            :class="{
              'score-high': scorePercentage >= 80,
              'score-medium': scorePercentage >= 50 && scorePercentage < 80,
              'score-low': scorePercentage < 50,
            }"
          ></div>
        </div>
      </div>

      <!-- Criteria checklist -->
      <div class="criteria-checklist">
        <CheckpointItem
          v-for="(checkpoint, index) in evaluationCriteriaQuery.data.value.checkpoints"
          :key="index"
          :number="index + 1"
          :criteria="checkpoint.criteria"
          :points="checkpoint.points"
          :result="hasResults ? evaluationResults[index] : undefined"
        />
      </div>

      <!-- Add the confirmation dialog component -->
      <ConfirmationDialog
        :isOpen="showDeleteDialog"
        :title="deleteOptions?.title || 'Delete Evaluation Criteria'"
        :message="
          deleteOptions?.message || 'Are you sure you want to delete this evaluation criteria?'
        "
        :confirmButtonText="deleteOptions?.confirmButtonText || 'Delete'"
        :isDangerous="true"
        :isLoading="deleteCriteriaMutation.isPending.value"
        @confirm="confirmDelete"
        @cancel="closeDeleteDialog"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { transformResults, type OldFormatData } from '@/helpers/transform-results'
import { useQuery, useMutation } from '@tanstack/vue-query'
import EvaluationCriteriaForm from '../EvaluationCriteriaForm.vue'
import { evaluationService } from '../../services/evaluationService'
import ConfirmationDialog from '../ConfirmationDialog.vue'
import CheckpointItem from '../CheckpointItem.vue'
import BaseButton from '../BaseButton.vue'
import { useEvaluationScores } from '@/composables/useEvaluationScores'
import { useDeleteConfirmation } from '@/composables/useDeleteConfirmation'
import { useQueryInvalidation } from '@/composables/useQueryInvalidation'
import { useNavigation } from '@/composables/useNavigation'
import { queryKeys } from '@/helpers/queryKeys'

interface Checkpoint {
  criteria: string
  points: number
}

interface EvaluationCriteria {
  llm_judge?: string
  checkpoints: Checkpoint[]
}

// Props
const props = defineProps<{
  workflowId: string
}>()

const isEditMode = ref(false)
const { invalidateEvaluationQueries, invalidateFileQueries, invalidateWorkflows } =
  useQueryInvalidation()
const { navigateToEvaluate } = useNavigation()

// Use delete confirmation composable
const { showDeleteDialog, deleteOptions, openDeleteDialog, closeDeleteDialog } =
  useDeleteConfirmation()

const toggleEditMode = () => {
  isEditMode.value = !isEditMode.value
}
// Handle criteria saved event
const onCriteriaSaved = () => {
  isEditMode.value = false
  invalidateEvaluationQueries(props.workflowId)
}

// Fetch evaluation criteria
const evaluationCriteriaQuery = useQuery({
  queryKey: queryKeys.evaluationCriteria(props.workflowId),
  queryFn: async (): Promise<EvaluationCriteria> => {
    return evaluationService.getEvaluationCriteria(props.workflowId)
  },
  retry: 1, // Retry once on failure
})

// Fetch evaluation results
const evaluationResultsQuery = useQuery({
  queryKey: queryKeys.evaluationResults(props.workflowId),
  queryFn: async (): Promise<OldFormatData> => {
    try {
      const data = await evaluationService.getEvaluationResults(props.workflowId)
      // Handle case where data might already be parsed or is an object
      const parsedData = typeof data === 'string' ? JSON.parse(data) : data
      return transformResults(parsedData)
    } catch {
      return {
        checkpoints: [],
        totalScore: 0,
        maxPossibleScore: 0,
        score: 0,
        maxScore: 0,
      }
    }
  },
  // No need to wait for criteria to load to fetch results
  enabled: computed(() => !!props.workflowId),
  // Don't retry too many times for results that might not exist yet
  retry: 1,
})

// Prepare evaluation results with proper alignment to criteria
const evaluationResults = computed(() => {
  if (!evaluationResultsQuery.data.value || !evaluationCriteriaQuery.data.value) {
    return []
  }

  const results = [...(evaluationResultsQuery.data.value.checkpoints || [])]

  // Ensure we have a result for each criterion
  if (evaluationCriteriaQuery.data.value.checkpoints.length > results.length) {
    // Pad with empty results if needed
    const missing = evaluationCriteriaQuery.data.value.checkpoints.length - results.length
    for (let i = 0; i < missing; i++) {
      results.push({ result: 'fail', feedback: '', criteria: '', points: 0 })
    }
  }

  return results
})

// Check if evaluation results are available
const hasResults = computed(() => {
  return (evaluationResultsQuery.data.value?.checkpoints?.length || 0) > 0
})

// Use evaluation scores composable for consistent calculations
const { totalPossiblePoints, totalScore, scorePercentage } = useEvaluationScores(
  evaluationCriteriaQuery.data,
  evaluationResultsQuery.data,
)

const hasCriteriaError = computed(
  () =>
    evaluationCriteriaQuery.isError.value &&
    (evaluationCriteriaQuery.error.value as { response?: { status?: number } })?.response
      ?.status === 404,
)

const startCreatingCriteria = () => {
  isEditMode.value = true
}
const deleteCriteriaMutation = useMutation({
  mutationFn: () => evaluationService.deleteEvaluationCriteria(props.workflowId),
  onSuccess: () => {
    invalidateEvaluationQueries(props.workflowId)
    invalidateFileQueries(props.workflowId, 'evaluation_case.json', 'evaluation_results.json')
    invalidateWorkflows()
    closeDeleteDialog()
    navigateToEvaluate(props.workflowId)
  },
})

// Functions for delete confirmation
const handleDeleteClick = () => {
  openDeleteDialog({
    title: 'Delete Evaluation Criteria',
    message:
      'Are you sure you want to delete this evaluation criteria? This will also delete any evaluation results. This action cannot be undone.',
    confirmButtonText: 'Delete',
  })
}

const confirmDelete = () => {
  deleteCriteriaMutation.mutate()
}
</script>

<style scoped>
.evaluation-criteria-viewer {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.criteria-content {
  display: flex;
  flex-direction: column;
  gap: 2rem; /* Spacing between content sections */
}

.criteria-loading,
.criteria-error,
.criteria-empty {
  text-align: center;
  padding: 2rem;
  font-size: 1.1rem;
}

.criteria-error {
  color: var(--color-error, #e74c3c);
}

.criteria-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background-color: var(--color-background-soft);
  border-radius: 8px;
  padding: 1.5rem;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.judge-info {
  margin: 0.5rem 0; /* Keep this small internal spacing */
}

.judge-label,
.points-label {
  font-weight: 500;
  margin-right: 0.5rem;
}

.judge-model {
  background-color: var(--color-background);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
}

.points-value {
  font-weight: 500;
}

.criteria-checklist {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.final-score {
  background-color: var(--color-background);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 2px solid var(--color-border);
}

/* Style for the success/error colors on the score */
.score-value {
  font-size: 2.2rem;
  font-weight: bold;
}

.score-display {
  display: flex;
  align-items: baseline;
  gap: 1rem; /* Already using gap - good! */
  margin: 1rem 0; /* Could convert to padding or parent gap */
}

.score-percentage {
  font-size: 1.2rem;
  font-weight: 500;
  color: var(--color-text-light, var(--color-text-secondary));
}

.score-bar {
  height: 8px;
  background-color: var(--color-background);
  border-radius: 4px;
  overflow: hidden;
}

.score-progress {
  height: 100%;
  transition: width 0.5s ease;
}

.score-high {
  background-color: var(--color-success, #2ecc71);
}

.score-medium {
  background-color: var(--color-warning, #f39c12);
}

.score-low {
  background-color: var(--color-error, #e74c3c);
}

.criteria-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.edit-button {
  /* padding: 0.6rem 1.2rem; */
  /* border-radius: 6px; */
  /* border: 1px solid var(--color-border); */
  /* background-color: var(--color-background); */
  /* cursor: pointer; */
}

.edit-button:hover {
  /* background-color: var(--color-background-soft); */
  /* border-color: var(--color-border-hover); */
}

.criteria-form-container {
  width: 100%;
}

.empty-criteria-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 2.5rem;
  text-align: center;
  background-color: var(--color-background-soft);
  border-radius: 8px;
}

.empty-criteria-message {
  max-width: 500px;
}

.empty-criteria-message h3 {
  margin-bottom: 0.75rem;
}

.empty-criteria-message p {
  color: var(--color-text-light);
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .checkpoint-header {
    flex-direction: column;
  }

  .checkpoint-number {
    margin-bottom: 0.5rem;
  }
}
</style>
