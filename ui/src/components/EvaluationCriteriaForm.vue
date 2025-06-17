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
              ></textarea>
            </div>

            <div class="form-group">
              <label :for="`points-${index}`">Points</label>
              <input
                :id="`points-${index}`"
                type="number"
                v-model.number="checkpoint.points"
                min="1"
                required
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
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useMutation } from '@tanstack/vue-query'
import { saveEvaluationCriteria } from '../services/evaluationService'
import type { EvaluationCriteria } from '../types/evaluation'

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

const saveMutation = useMutation({
  mutationFn: async () => {
    return await saveEvaluationCriteria(props.workflowPath, formData)
  },
  onSuccess: () => {
    emit('saved', true)
  },
  onError: (error) => {
    console.error('Failed to save criteria:', error)
    emit('saved', false)
  },
})

const handleSubmit = () => {
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
  display: flex;
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
}

.delete-button:hover {
  background-color: rgba(231, 76, 60, 0.15);
  color: var(--color-error, #e74c3c);
  border-color: var(--color-error, #e74c3c);
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

/* Add these styles for the warning message */
.form-warning {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  margin-bottom: 1.5rem;
  background-color: rgba(243, 156, 18, 0.1);
  border-left: 4px solid #f39c12;
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
</style>
