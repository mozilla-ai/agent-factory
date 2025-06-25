<template>
  <div class="evaluation-panel">
    <div v-if="allEvaluationFilesExist" class="evaluation-status success">
      <span class="success-icon">✓</span>
      <span class="status-text">All evaluation files are already generated</span>
      <BaseButton
        variant="primary"
        @click="viewResults"
        :disabled="!evaluationStatus?.hasEvalResults"
      >
        View Results
      </BaseButton>
    </div>

    <div class="evaluation-steps">
      <EvaluationStepButton
        :step-number="1"
        title="Run Agent"
        description="Execute the agent to generate a trace file"
        :is-completed="evaluationStatus.hasAgentTrace"
        :is-loading="runAgentMutation.isPending.value"
        :has-error="runAgentMutation.isError.value"
        :is-disabled="
          runAgentMutation.isPending.value ||
          genCasesMutation.isPending.value ||
          runEvalMutation.isPending.value
        "
        @click="runAgentMutation.mutate()"
      />

      <EvaluationStepButton
        :step-number="2"
        title="Generate Evaluation Cases"
        description="Create test cases to evaluate the agent"
        :is-completed="evaluationStatus.hasEvalCases"
        :is-loading="genCasesMutation.isPending.value"
        :has-error="genCasesMutation.isError.value"
        :is-disabled="
          runAgentMutation.isPending.value ||
          genCasesMutation.isPending.value ||
          runEvalMutation.isPending.value
        "
        @click="genCasesMutation.mutate()"
      />

      <EvaluationStepButton
        :step-number="3"
        title="Run Evaluation"
        description="Evaluate the agent against test cases"
        :is-completed="evaluationStatus.hasEvalResults"
        :is-loading="runEvalMutation.isPending.value"
        :has-error="runEvalMutation.isError.value"
        :is-disabled="
          runAgentMutation.isPending.value ||
          genCasesMutation.isPending.value ||
          runEvalMutation.isPending.value ||
          !evaluationStatus.hasAgentTrace ||
          !evaluationStatus.hasEvalCases
        "
        @click="runEvalMutation.mutate()"
      />
    </div>

    <StreamingOutput
      v-if="output || isProcessing || hasAnyError"
      title="Output"
      :content="output || errorMessage"
      :is-loading="isProcessing"
      max-height="300px"
    >
      <template #actions>
        <BaseButton variant="ghost" size="small" @click="clearOutput()">Clear</BaseButton>
      </template>
    </StreamingOutput>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, ref } from 'vue'
import { useMutation } from '@tanstack/vue-query'
import { evaluationService } from '@/services/evaluationService'
import { useStreamProcessor } from '@/composables/useStreamProcessor'
import { useQueryInvalidation } from '@/composables/useQueryInvalidation'
import { useNavigation } from '@/composables/useNavigation'
import EvaluationStepButton from '../EvaluationStepButton.vue'
import BaseButton from '../BaseButton.vue'
import StreamingOutput from '../StreamingOutput.vue'

const props = defineProps({
  workflowId: {
    type: String,
    required: true,
  },
  evaluationStatus: {
    type: Object,
    default: () => ({
      hasAgentTrace: false,
      hasEvalCases: false,
      hasEvalResults: false,
    }),
  },
})

const { invalidateEvaluationQueries, invalidateFileQueries, invalidateWorkflows } =
  useQueryInvalidation()
const { navigateToResults } = useNavigation()
const { output, clearOutput, processStream, isProcessing } = useStreamProcessor()

const errorMessage = ref('')

// Computed property to check if all evaluation files exist
const allEvaluationFilesExist = computed(
  () =>
    props.evaluationStatus.hasAgentTrace &&
    props.evaluationStatus.hasEvalCases &&
    props.evaluationStatus.hasEvalResults,
)

// Individual mutations using TanStack Query directly
const runAgentMutation = useMutation({
  mutationFn: async () => {
    clearOutput()
    errorMessage.value = ''
    const stream = await evaluationService.runAgent(props.workflowId)
    await processStream(stream)
  },
  onSuccess: () => {
    invalidateEvaluationQueries(props.workflowId)
    invalidateFileQueries(props.workflowId, 'agent_eval_trace.json')
    invalidateWorkflows()
  },
  onError: (error) => {
    console.error('Run agent error:', error)
    errorMessage.value = `Failed to run agent: ${error.message}`
  },
})

const genCasesMutation = useMutation({
  mutationFn: async () => {
    clearOutput()
    errorMessage.value = ''
    const stream = await evaluationService.generateEvaluationCases(props.workflowId)
    await processStream(stream)
  },
  onSuccess: () => {
    invalidateEvaluationQueries(props.workflowId)
    invalidateFileQueries(props.workflowId, 'evaluation_case.yaml')
    invalidateWorkflows()
  },
  onError: (error) => {
    console.error('Generate cases error:', error)
    errorMessage.value = `Failed to generate evaluation cases: ${error.message}`
  },
})

const runEvalMutation = useMutation({
  mutationFn: async () => {
    clearOutput()
    errorMessage.value = ''
    const stream = await evaluationService.runEvaluation(props.workflowId)
    await processStream(stream)
  },
  onSuccess: () => {
    invalidateEvaluationQueries(props.workflowId)
    invalidateFileQueries(props.workflowId, 'evaluation_results.json')
    invalidateWorkflows()
  },
  onError: (error) => {
    console.error('Run evaluation error:', error)
    errorMessage.value = `Failed to run evaluation: ${error.message}`
  },
})

const hasAnyError = computed(
  () =>
    runAgentMutation.isError.value ||
    genCasesMutation.isError.value ||
    runEvalMutation.isError.value ||
    errorMessage.value,
)

function viewResults() {
  navigateToResults(props.workflowId)
}
</script>

<style scoped>
.evaluation-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.evaluation-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  background-color: var(--color-success-background, rgba(0, 128, 0, 0.1));
  border: 1px solid var(--color-success, green);
}

.success-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  background-color: var(--color-success, green);
  color: white;
  font-weight: bold;
}

.status-text {
  flex: 1;
  font-weight: 500;
  color: var(--color-text);
}

.evaluation-steps {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
</style>
