<template>
  <div class="evaluation-panel">
    <div v-if="allEvaluationFilesExist" class="evaluation-status success">
      <span class="success-icon">✓</span>
      <span class="status-text">All evaluation files are already generated</span>
      <button
        class="action-button"
        @click="viewResults"
        :disabled="!evaluationStatus?.hasEvalResults"
      >
        View Results
      </button>
    </div>

    <div class="evaluation-steps">
      <button
        @click="runAgentMutation.mutate()"
        :disabled="
          runAgentMutation.isPending.value ||
          genCasesMutation.isPending.value ||
          runEvalMutation.isPending.value
        "
        class="eval-button"
        :class="{ completed: evaluationStatus.hasAgentTrace }"
      >
        <span class="step-number">1</span>
        <div class="step-content">
          <h4>Run Agent</h4>
          <p>Execute the agent to generate a trace file</p>
        </div>
        <div class="step-status">
          <span v-if="runAgentMutation.isPending.value" class="loading-indicator">⏳</span>
          <span v-else-if="evaluationStatus.hasAgentTrace" class="success-indicator">✓</span>
        </div>
      </button>

      <button
        @click="genCasesMutation.mutate()"
        :disabled="
          runAgentMutation.isPending.value ||
          genCasesMutation.isPending.value ||
          runEvalMutation.isPending.value
        "
        class="eval-button"
        :class="{ completed: evaluationStatus.hasEvalCases }"
      >
        <span class="step-number">2</span>
        <div class="step-content">
          <h4>Generate Evaluation Cases</h4>
          <p>Create test cases to evaluate the agent</p>
        </div>
        <div class="step-status">
          <span v-if="genCasesMutation.isPending.value" class="loading-indicator">⏳</span>
          <span v-else-if="evaluationStatus.hasEvalCases" class="success-indicator">✓</span>
        </div>
      </button>

      <button
        @click="runEvalMutation.mutate()"
        :disabled="
          runAgentMutation.isPending.value ||
          genCasesMutation.isPending.value ||
          runEvalMutation.isPending.value ||
          !evaluationStatus.hasAgentTrace ||
          !evaluationStatus.hasEvalCases
        "
        class="eval-button"
        :class="{ completed: evaluationStatus.hasEvalResults }"
      >
        <span class="step-number">3</span>
        <div class="step-content">
          <h4>Run Evaluation</h4>
          <p>Evaluate the agent against test cases</p>
        </div>
        <div class="step-status">
          <span v-if="runEvalMutation.isPending.value" class="loading-indicator">⏳</span>
          <span v-else-if="evaluationStatus.hasEvalResults" class="success-indicator">✓</span>
        </div>
      </button>
    </div>

    <div v-if="output" class="evaluation-output">
      <div class="output-header">
        <h3>Output</h3>
        <button @click="output = ''" class="clear-button">Clear</button>
      </div>
      <pre class="output-content">{{ output }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, defineProps, defineEmits, watch } from 'vue'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { evaluationService } from '@/services/evaluationService'

const props = defineProps({
  workflowPath: {
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

const emit = defineEmits(['evaluation-status-changed'])
const queryClient = useQueryClient()
const router = useRouter()
const output = ref('')

// Computed property to check if all evaluation files exist
const allEvaluationFilesExist = computed(
  () =>
    props.evaluationStatus.hasAgentTrace &&
    props.evaluationStatus.hasEvalCases &&
    props.evaluationStatus.hasEvalResults,
)

// Watch for workflow path changes
// watch(
//   () => props.workflowPath,
//   (newPath) => {
//     console.log('Workflow path changed to:', newPath)
//   },
// )

// Process streaming response
async function processStreamingResponse(response: Response): Promise<void> {
  const reader = response.body?.getReader()
  if (!reader) {
    output.value += 'Error: No response body\n'
    return
  }

  const decoder = new TextDecoder()
  let done = false

  while (!done) {
    const { value, done: streamDone } = await reader.read()
    if (value) {
      const chunk = decoder.decode(value, { stream: true })
      output.value += chunk
    }
    done = streamDone
  }
}

// Mutations for evaluation steps
const runAgentMutation = useMutation({
  mutationFn: async () => {
    output.value = `Running agent for workflow: ${props.workflowPath}...\n`

    try {
      const stream = await evaluationService.runAgent(props.workflowPath)
      await processStream(stream)
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      output.value += `Error: ${errorMessage}\n`
      throw error
    }
  },
  onSuccess: () => {
    console.log('Agent run successful, invalidating evaluation status query')
    queryClient.invalidateQueries({
      queryKey: ['evaluationStatus', props.workflowPath],
    })
    emit('evaluation-status-changed', {
      hasAgentTrace: true,
    })
  },
  onError: (error) => {
    console.error('Error running agent:', error)
  },
})

const genCasesMutation = useMutation({
  mutationFn: async () => {
    output.value = 'Generating evaluation cases...\n'

    try {
      const stream = await evaluationService.generateEvaluationCases(props.workflowPath)
      await processStream(stream)
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      output.value += `Error: ${errorMessage}\n`
      throw error
    }
  },
  onSuccess: () => {
    console.log('Case generation successful, invalidating cases query')
    queryClient.invalidateQueries({
      queryKey: ['evaluationStatus', props.workflowPath],
    })
    emit('evaluation-status-changed', {
      hasEvalCases: true,
    })
  },
  onError: (error) => {
    console.error('Error generating cases:', error)
  },
})

const runEvalMutation = useMutation({
  mutationFn: async () => {
    output.value = `Running evaluation for workflow: ${props.workflowPath}...\n`

    try {
      const stream = await evaluationService.runEvaluation(props.workflowPath)
      await processStream(stream)
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      output.value += `Error: ${errorMessage}\n`
      throw error
    }
  },
  onSuccess: () => {
    console.log('Evaluation successful, invalidating results query')
    queryClient.invalidateQueries({
      queryKey: ['evaluationStatus', props.workflowPath],
    })
    emit('evaluation-status-changed', {
      hasEvalResults: true,
    })
  },
  onError: (error) => {
    console.error('Error running evaluation:', error)
  },
})

// Helper function to process streams from axios responses
async function processStream(stream: ReadableStream) {
  const reader = stream.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    output.value += decoder.decode(value, { stream: true })
  }
}

function viewResults() {
  router.push({
    path: router.currentRoute.value.path,
    query: { ...router.currentRoute.value.query, tab: 'results' },
  })
}

onMounted(() => {
  console.log('Component mounted with workflow path:', props.workflowPath)
})
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

/* Replace the action-button styles to use defined variables */
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

.action-button:disabled {
  background: var(--button-disabled-background-color);
  border-color: var(--color-border);
  color: var(--button-disabled-text-color);
  cursor: not-allowed;
}

.evaluation-steps {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Higher contrast for buttons */
.eval-button {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-background);
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.eval-button:not(:disabled):hover {
  border-color: var(--color-border-hover);
  background-color: var(--color-background-hover);
}

.eval-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.eval-button.completed {
  border-color: var(--color-success, green);
  background-color: var(--color-success-background, rgba(0, 128, 0, 0.1));
  box-shadow: 0 0 0 1px var(--color-success, green);
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background-color: var(--color-background-soft);
  color: var(--color-text); /* Ensure text uses main color */
  font-weight: bold;
  border: 1px solid var(--color-border);
}

.step-content {
  flex: 1;
}

.step-content h4 {
  margin: 0 0 0.25rem;
  color: var(--color-heading, var(--color-text)); /* Use heading color if available */
}

.step-content p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-secondary); /* Use the existing secondary text color */
}

.step-status {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
}

.loading-indicator,
.success-indicator {
  font-size: 1.25rem;
}

.success-indicator {
  color: var(--color-success, green);
  font-size: 1.4rem;
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
  color: var(--color-heading, var(--color-text)); /* Use heading color if available */
  font-weight: 600;
}

.clear-button {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  cursor: pointer;
  color: var(--color-text);
}

.clear-button:hover {
  background-color: var(--color-background-mute);
  border-color: var(--color-border-hover);
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
  color: var(--color-text); /* Ensure text color has good contrast */
  border-top: 1px solid var(--color-border); /* Add subtle separator */
}
</style>
