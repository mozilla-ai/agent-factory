<template>
  <div class="evaluation-criteria-form">
    <h3>{{ initialData ? 'Edit' : 'Create' }} Evaluation Criteria</h3>
    <div class="form-warning">
      <div class="warning-icon">⚠️</div>
      <div class="warning-text">
        <strong>Warning:</strong> Saving criteria will invalidate any existing evaluation results
        for this workflow. Previous results will be deleted as they would no longer match the
        updated criteria.
      </div>
    </div>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="llm-judge">LLM Judge</label>
        <select id="llm-judge" v-model="formData.llm_judge" required>
          <option value="openai/gpt-4.1">OpenAI GPT-4.1</option>
          <option value="openai/gpt-4">OpenAI GPT-4</option>
          <option value="anthropic/claude-3-opus">Anthropic Claude 3 Opus</option>
          <option value="anthropic/claude-3-sonnet">Anthropic Claude 3 Sonnet</option>
        </select>
      </div>

      <div class="checkpoints-section">
        <h4>Evaluation Checkpoints</h4>
        <p class="help-text">Define the criteria used to evaluate agent performance</p>

        <div
          v-for="(checkpoint, index) in formData.checkpoints"
          :key="index"
          class="checkpoint-item"
        >
          <div class="checkpoint-header">
            <div class="checkpoint-number">{{ index + 1 }}</div>
            <div class="checkpoint-actions">
              <button
                type="button"
                class="delete-button"
                @click="removeCheckpoint(index)"
                aria-label="Remove checkpoint"
              >
                <span aria-hidden="true">×</span>
              </button>
            </div>
          </div>

          <div class="checkpoint-content">
            <div class="form-group">
              <label :for="`criteria-${index}`">Criteria</label>
              <textarea
                :id="`criteria-${index}`"
                v-model="checkpoint.criteria"
                rows="3"
                placeholder="Describe what the agent should accomplish"
                required
                :class="{ 'input-error': formErrors.checkpoints[index] }"
              ></textarea>
              <div v-if="formErrors.checkpoints[index]" class="error-message">
                {{ formErrors.checkpoints[index] }}
              </div>
            </div>

            <div class="form-group">
              <label :for="`points-${index}`">Points</label>
              <input
                :id="`points-${index}`"
                type="number"
                v-model.number="checkpoint.points"
                min="1"
                max="10"
                required
                :class="{ 'input-error': formErrors.checkpoints[index] }"
              />
            </div>
          </div>
        </div>

        <button type="button" class="add-checkpoint-button" @click="addCheckpoint">
          Add Checkpoint
        </button>
      </div>

      <div class="form-actions">
        <button type="button" class="cancel-button" @click="emit('cancel')">Cancel</button>
        <button type="submit" class="save-button" :disabled="saveMutation.isPending.value">
          {{ saveMutation.isPending.value ? 'Saving...' : 'Save Criteria' }}
        </button>
      </div>
    </form>

    <!-- Add toast notification -->
    <div
      v-if="showToast"
      class="toast-notification"
      :class="{ 'toast-success': toastType === 'success', 'toast-error': toastType === 'error' }"
    >
      {{ toastMessage }}
      <button class="toast-close" @click="showToast = false">&times;</button>
    </div>

    <!-- Add retry mechanism if the save fails -->
    <div v-if="saveMutation.isError.value" class="save-error-container">
      <div class="save-error-message">
        <div class="error-icon">❌</div>
        <div>{{ saveMutation.error.value?.message || 'Error saving criteria' }}</div>
      </div>
      <div class="save-error-actions">
        <button type="button" class="retry-button" @click="handleSubmit">Retry Saving</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { saveEvaluationCriteria } from '../services/evaluationService'
import type { EvaluationCriteria } from '../types/evaluation'
import { useWorkflowsStore } from '@/stores/workflows'

const props = defineProps<{
  workflowPath: string
  initialData?: EvaluationCriteria | null
}>()

const emit = defineEmits<{
  saved: [success: boolean]
  cancel: []
}>()

const formData = reactive<EvaluationCriteria>({
  llm_judge: 'openai/gpt-4.1',
  checkpoints: [
    {
      criteria: '',
      points: 2,
    },
  ],
})

// Add validation state
const formErrors = ref({
  checkpoints: [] as string[],
})

// Add validation function
const validateForm = () => {
  let isValid = true
  formErrors.value.checkpoints = []

  // Reset all errors
  formErrors.value.checkpoints = Array(formData.checkpoints.length).fill('')

  // Validate each checkpoint
  formData.checkpoints.forEach((checkpoint, index) => {
    if (!checkpoint.criteria.trim()) {
      formErrors.value.checkpoints[index] = 'Criteria description is required'
      isValid = false
    } else if (checkpoint.criteria.trim().length < 10) {
      formErrors.value.checkpoints[index] = 'Criteria must be at least 10 characters'
      isValid = false
    }

    if (checkpoint.points < 1 || checkpoint.points > 10) {
      formErrors.value.checkpoints[index] = 'Points must be between 1 and 10'
      isValid = false
    }
  })

  return isValid
}

onMounted(() => {
  if (props.initialData) {
    formData.llm_judge = props.initialData.llm_judge
    formData.checkpoints = [...props.initialData.checkpoints]
  }
})

const addCheckpoint = () => {
  formData.checkpoints.push({
    criteria: '',
    points: 2,
  })
}

const removeCheckpoint = (index: number) => {
  formData.checkpoints.splice(index, 1)
}

const queryClient = useQueryClient()
const workflowsStore = useWorkflowsStore()

// Add toast notification state
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref('error') // 'success' or 'error'
// Update mutation with better error handling
const saveMutation = useMutation({
  mutationFn: async () => {
    try {
      return await saveEvaluationCriteria(props.workflowPath, formData)
    } catch (error: unknown) {
      // Handle specific error types
      const err = error as { response?: { status?: number }; message?: string }
      if (err.response?.status === 403) {
        throw new Error('You do not have permission to save evaluation criteria')
      } else if (err.response?.status === 404) {
        throw new Error('Workflow not found - please check the path and try again')
      } else if (err.response?.status === 500) {
        throw new Error('Server error while saving criteria - please try again later')
      } else {
        throw new Error(`Failed to save criteria: ${err.message || 'Unknown error'}`)
      }
    }
  },
  onSuccess: () => {
    // Success notification
    toastMessage.value = 'Evaluation criteria saved successfully!'
    toastType.value = 'success'
    showToast.value = true

    // Close toast after 5 seconds
    setTimeout(() => {
      showToast.value = false
    }, 5000)

    // Invalidate the criteria query to refresh data
    queryClient.invalidateQueries({
      queryKey: ['evaluation-criteria', props.workflowPath],
    })
    queryClient.invalidateQueries({
      queryKey: ['evaluation-status', props.workflowPath],
    })
    queryClient.invalidateQueries({
      queryKey: ['file-content', props.workflowPath],
    })
    queryClient.invalidateQueries({
      queryKey: ['file-content', props.workflowPath, 'evaluation_case.json'],
    })
    // Refresh the workflow store to update file explorer
    workflowsStore.loadWorkflows()
    emit('saved', true)
  },
  onError: (error) => {
    console.error('Failed to save criteria:', error)

    // Error notification
    toastMessage.value = error.message || 'Failed to save evaluation criteria'
    toastType.value = 'error'
    showToast.value = true

    // Close toast after 8 seconds for errors
    setTimeout(() => {
      showToast.value = false
    }, 8000)

    emit('saved', false)
  },
})

// Update the submission handler
const handleSubmit = () => {
  if (!validateForm()) {
    return
  }
  saveMutation.mutate()
}
</script>

<style scoped>
.evaluation-criteria-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-weight: 500;
  color: var(--color-text);
}

input,
textarea,
select {
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background-color: var(--color-background);
  color: var(--color-text);
  font-family: inherit;
  font-size: 1rem;
}

input:focus,
textarea:focus,
select:focus {
  outline: 2px solid var(--color-border-hover);
  border-color: var(--color-border-hover);
}

.checkpoints-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.help-text {
  color: var(--color-text-light);
  font-size: 0.9rem;
}

.checkpoint-item {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background-color: var(--color-background-soft);
}

.checkpoint-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
}

.checkpoint-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  background-color: var(--color-background);
  border-radius: 50%;
  font-weight: bold;
  border: 1px solid var(--color-border);
}

.checkpoint-content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.checkpoint-actions {
  display: flex;
  gap: 0.5rem;
}

.delete-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  background-color: var(--color-background);
  color: var(--color-text);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0;
}

.delete-button:hover:not(:disabled) {
  background-color: var(--color-error-soft);
  color: var(--color-error);
  border-color: var(--color-error);
}

.add-checkpoint-button {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  border: 1px dashed var(--color-border);
  background-color: var(--color-background);
  color: var(--color-text);
  cursor: pointer;
  text-align: center;
  font-weight: 500;
}

.add-checkpoint-button:hover {
  border-color: var(--color-border-hover);
  background-color: var(--color-background-soft);
}

/* Update warning style to use CSS variables */
.form-warning {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  margin-bottom: 1.5rem;
  background-color: var(--color-warning-soft);
  border-left: 4px solid var(--color-warning);
  border-radius: 4px;
}

.warning-icon {
  font-size: 1.25rem;
  line-height: 1.2;
}

.warning-text {
  font-size: 0.9rem;
  color: var(--color-text);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.cancel-button {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background-color: var(--color-background);
  color: var(--color-text);
  font-weight: 500;
  cursor: pointer;
}

.cancel-button:hover {
  background-color: var(--color-background-soft);
}

.save-button {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  border: none;
  font-weight: 600;
  cursor: pointer;
}

.save-button:hover:not(:disabled) {
  opacity: 0.9;
}

.save-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Add error styling */
.input-error {
  border-color: var(--color-error) !important;
  background-color: var(--color-error-soft) !important;
}

.error-message {
  color: var(--color-error);
  font-size: 0.8rem;
  margin-top: 0.25rem;
}

/* Toast notifications */
.toast-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 1rem 1.5rem;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 300px;
  max-width: 500px;
}

.toast-success {
  background-color: var(--color-success-soft);
  border-left: 4px solid var(--color-success);
  color: var(--color-success);
}

.toast-error {
  background-color: var(--color-error-soft);
  border-left: 4px solid var(--color-error);
  color: var(--color-error);
}

.toast-close {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: inherit;
}

/* Error display */
.save-error-container {
  margin: 1rem 0;
  padding: 1rem;
  background-color: var(--color-error-soft);
  border-radius: 4px;
  border-left: 4px solid var(--color-error);
}

.save-error-message {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.save-error-actions {
  display: flex;
  justify-content: flex-end;
}

.retry-button {
  padding: 0.5rem 1rem;
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
}

.retry-button:hover {
  background-color: var(--color-background-soft);
}
</style>
