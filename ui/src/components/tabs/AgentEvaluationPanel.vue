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

    <div v-if="output || isProcessing" class="evaluation-output">
      <div class="output-header">
        <h3>Output</h3>
        <BaseButton variant="ghost" size="small" @click="clearOutput()">Clear</BaseButton>
      </div>

      <div v-if="isProcessing && !output" class="loading-state">
        <span class="loading-indicator">Processing...</span>
      </div>

      <div v-if="output" class="output-content-container">
        <pre class="output-content">{{ output }}</pre>

        <!-- Show streaming indicator while processing -->
        <div v-if="isProcessing" class="streaming-indicator">
          <span class="loading-indicator">Streaming...</span>
          <div class="streaming-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps } from 'vue'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { evaluationService } from '@/services/evaluationService'
import { useWorkflows } from '@/composables/useWorkflows'
import { useStreamProcessor } from '@/composables/useStreamProcessor'
import { queryKeys } from '@/helpers/queryKeys'
import EvaluationStepButton from '../EvaluationStepButton.vue'
import BaseButton from '../BaseButton.vue'

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

const router = useRouter()
const queryClient = useQueryClient()
const { invalidateWorkflows } = useWorkflows()
const { output, clearOutput, processStream, isProcessing } = useStreamProcessor()

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
    const stream = await evaluationService.runAgent(props.workflowId)
    await processStream(stream)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({
      queryKey: queryKeys.evaluationStatus(props.workflowId),
    })
    queryClient.invalidateQueries({
      queryKey: queryKeys.fileContent(props.workflowId, 'agent_eval_trace.json'),
    })
    invalidateWorkflows()
  },
})

const genCasesMutation = useMutation({
  mutationFn: async () => {
    clearOutput()
    const stream = await evaluationService.generateEvaluationCases(props.workflowId)
    await processStream(stream)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({
      queryKey: queryKeys.evaluationStatus(props.workflowId),
    })
    queryClient.invalidateQueries({
      queryKey: queryKeys.fileContent(props.workflowId, 'evaluation_case.yaml'),
    })
    invalidateWorkflows()
  },
})

const runEvalMutation = useMutation({
  mutationFn: async () => {
    clearOutput()
    const stream = await evaluationService.runEvaluation(props.workflowId)
    await processStream(stream)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({
      queryKey: queryKeys.evaluationStatus(props.workflowId),
    })
    queryClient.invalidateQueries({
      queryKey: queryKeys.fileContent(props.workflowId, 'evaluation_results.json'),
    })
    invalidateWorkflows()
  },
})

function viewResults() {
  router.push({
    path: router.currentRoute.value.path,
    query: { ...router.currentRoute.value.query, tab: 'results' },
  })
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

.evaluation-output {
  margin-top: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
}

.output-header h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--color-heading, var(--color-text));
  font-weight: 600;
}

.loading-state {
  display: flex;
  align-items: center;
  padding: 1rem;
  font-style: italic;
  color: var(--color-text-secondary);
  background: var(--color-background);
}

.loading-state .loading-indicator::before {
  content: '⏳ ';
  margin-right: 0.5rem;
}

.output-content-container {
  position: relative;
}

.output-content {
  padding: 1rem;
  margin: 0;
  max-height: 300px;
  overflow: auto;
  font-family: monospace;
  font-size: 0.9rem;
  white-space: pre-wrap;
  background-color: var(--color-background);
  color: var(--color-text);
}

.streaming-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border-top: 1px solid var(--color-border);
  font-style: italic;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.streaming-dots {
  display: flex;
  gap: 0.2rem;
}

.streaming-dots span {
  width: 0.25rem;
  height: 0.25rem;
  background: var(--color-primary);
  border-radius: 50%;
  animation: streaming-pulse 1.5s infinite;
}

.streaming-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.streaming-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes streaming-pulse {
  0%,
  60%,
  100% {
    opacity: 0.3;
    transform: scale(1);
  }
  30% {
    opacity: 1;
    transform: scale(1.2);
  }
}
</style>
