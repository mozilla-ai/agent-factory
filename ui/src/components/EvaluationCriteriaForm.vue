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
      <FormField
        v-model="formData.llm_judge"
        label="LLM Judge"
        type="select"
        required
        field-id="llm-judge"
        :options="[
          { value: 'openai/gpt-4.1', label: 'OpenAI GPT-4.1' },
          { value: 'openai/gpt-4', label: 'OpenAI GPT-4' },
          { value: 'anthropic/claude-3-opus', label: 'Anthropic Claude 3 Opus' },
          { value: 'anthropic/claude-3-sonnet', label: 'Anthropic Claude 3 Sonnet' },
        ]"
      />

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
            <FormField
              v-model="checkpoint.criteria"
              label="Criteria"
              type="textarea"
              placeholder="Describe what the agent should accomplish"
              required
              :rows="3"
              :field-id="`criteria-${index}`"
              :error="formErrors.checkpoints[index]"
            />

            <FormField
              v-model="checkpoint.points"
              label="Points"
              type="number"
              required
              :min="1"
              :max="10"
              :field-id="`points-${index}`"
              :error="formErrors.checkpoints[index]"
            />
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
import { useMutation } from '@tanstack/vue-query'
import type { EvaluationCriteria } from '../types/index'
import { evaluationService } from '@/services/evaluationService'
import { handleHttpError } from '@/helpers/error.helpers'
import { useQueryInvalidation } from '@/composables/useQueryInvalidation'
import FormField from './FormField.vue'

const props = defineProps<{
  workflowId: string
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

const formErrors = ref({
  checkpoints: [] as string[],
})

const validateForm = () => {
  let isValid = true
  formErrors.value.checkpoints = []

  formErrors.value.checkpoints = Array(formData.checkpoints.length).fill('')

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

const { invalidateEvaluationQueries, invalidateFileQueries, invalidateWorkflows } =
  useQueryInvalidation()

// Update mutation with better error handling
const saveMutation = useMutation({
  mutationFn: async () => {
    try {
      return await evaluationService.saveEvaluationCriteria(props.workflowId, formData)
    } catch (error: unknown) {
      handleHttpError(error, 'saving evaluation criteria')
    }
  },
  onSuccess: () => {
    invalidateEvaluationQueries(props.workflowId)
    invalidateFileQueries(props.workflowId, '', 'evaluation_case.json')
    invalidateWorkflows()
    emit('saved', true)
  },
  onError: (error) => {
    console.error('Failed to save criteria:', error)
    emit('saved', false)
  },
})

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
