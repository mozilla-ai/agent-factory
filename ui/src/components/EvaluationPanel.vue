<template>
  <div class="evaluation-panel">
    <div v-if="allEvaluationFilesExist" class="evaluation-status success">
      <span class="success-icon">✓</span>
      <span class="status-text">All evaluation files are already generated</span>
      <button
        @click="$emit('evaluation-status-changed', { tab: 'results' })"
        class="view-results-button"
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
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'

const props = defineProps<{
  workflowPath: string
}>()

const emit = defineEmits(['evaluation-status-changed'])
const queryClient = useQueryClient()
const output = ref('')

// Evaluation status tracking
const evaluationStatus = ref({
  hasAgentTrace: false,
  hasEvalCases: false,
  hasEvalResults: false,
})

// Computed property to check if all evaluation files exist
const allEvaluationFilesExist = computed(
  () =>
    evaluationStatus.value.hasAgentTrace &&
    evaluationStatus.value.hasEvalCases &&
    evaluationStatus.value.hasEvalResults,
)

// Debug logging
const debug = ref(true)

function log(...args: any[]) {
  if (debug.value) {
    console.log('[EvaluationPanel]', ...args)
  }
}

// Watch for workflow path changes
watch(
  () => props.workflowPath,
  (newPath) => {
    log('Workflow path changed to:', newPath)
  },
)

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

// FIXED: Check for specific files directly using the file access API
// not the directory API which doesn't exist
const agentTraceQuery = useQuery({
  queryKey: ['fileExists', 'agent_eval_trace.json', props.workflowPath],
  queryFn: async () => {
    // Use the direct file path for the trace
    const filePath = `${props.workflowPath}/agent_eval_trace.json`
    log('Checking agent trace file at:', filePath)
    try {
      const response = await fetch(`http://localhost:3000/agent-factory/workflows/${filePath}`, {
        method: 'HEAD',
      })
      return response.ok
    } catch (e) {
      console.error('Error checking agent trace:', e)
      return false
    }
  },
  enabled: !!props.workflowPath,
})

const evalCasesQuery = useQuery({
  queryKey: ['fileExists', 'evaluation_case.yaml', props.workflowPath],
  queryFn: async () => {
    // Use workflow-specific path for evaluation cases
    const filePath = `${props.workflowPath}/evaluation_case.yaml`
    log('Checking evaluation cases file at:', filePath)
    try {
      const response = await fetch(`http://localhost:3000/agent-factory/workflows/${filePath}`, {
        method: 'HEAD',
      })
      return response.ok
    } catch (e) {
      return false
    }
  },
  enabled: !!props.workflowPath,
})

const evalResultsQuery = useQuery({
  queryKey: ['fileExists', 'evaluation_results.json', props.workflowPath],
  queryFn: async () => {
    // Use workflow-specific path for evaluation results
    const filePath = `${props.workflowPath}/evaluation_results.json`
    log('Checking evaluation results file at:', filePath)
    try {
      const response = await fetch(`http://localhost:3000/agent-factory/workflows/${filePath}`, {
        method: 'HEAD',
      })
      return response.ok
    } catch (e) {
      return false
    }
  },
  enabled: !!props.workflowPath,
})

// Mutations for evaluation steps
const runAgentMutation = useMutation({
  mutationFn: async () => {
    output.value = `Running agent for workflow: ${props.workflowPath}...\n`

    log(`Sending run agent request for: ${props.workflowPath}`)
    const response = await fetch(
      `http://localhost:3000/agent-factory/evaluate/run-agent/${props.workflowPath}`,
      { method: 'POST' },
    )

    if (!response.ok) {
      const errorText = await response.text()
      output.value += `Error: ${response.status} ${response.statusText}\n${errorText}\n`
      throw new Error(`Failed to run agent: ${response.status} ${response.statusText}`)
    }

    await processStreamingResponse(response)
    return true
  },
  onSuccess: () => {
    log('Agent run successful, invalidating evaluation status query')
    // Emit that evaluation status has changed
    emit('evaluation-status-changed', {
      hasAgentTrace: true,
    })
  },
  onError: (error) => {
    console.error('Error running agent:', error)
    output.value += `Failed to run agent. Check console for details.\n`
  },
})

const genCasesMutation = useMutation({
  mutationFn: async () => {
    output.value = 'Generating evaluation cases...\n'

    log('Sending generate cases request')
    const response = await fetch('http://localhost:3000/agent-factory/evaluate/generate-cases', {
      method: 'POST',
    })

    if (!response.ok) {
      const errorText = await response.text()
      output.value += `Error: ${response.status} ${response.statusText}\n${errorText}\n`
      throw new Error(`Failed to generate cases: ${response.status} ${response.statusText}`)
    }

    await processStreamingResponse(response)
    return true
  },
  onSuccess: () => {
    log('Case generation successful, invalidating cases query')
    queryClient.invalidateQueries({
      queryKey: ['fileExists', 'evaluation_case.yaml', props.workflowPath],
    })
  },
  onError: (error) => {
    console.error('Error generating cases:', error)
    output.value += `Failed to generate cases. Check console for details.\n`
  },
})

const runEvalMutation = useMutation({
  mutationFn: async () => {
    output.value = `Running evaluation for workflow: ${props.workflowPath}...\n`

    log(`Sending run evaluation request for: ${props.workflowPath}`)
    const response = await fetch(
      `http://localhost:3000/agent-factory/evaluate/run-evaluation/${props.workflowPath}`,
      { method: 'POST' },
    )

    if (!response.ok) {
      const errorText = await response.text()
      output.value += `Error: ${response.status} ${response.statusText}\n${errorText}\n`
      throw new Error(`Failed to run evaluation: ${response.status} ${response.statusText}`)
    }

    await processStreamingResponse(response)
    return true
  },
  onSuccess: () => {
    log('Evaluation successful, invalidating results query')
    queryClient.invalidateQueries({
      queryKey: ['fileExists', 'evaluation_results.json', props.workflowPath],
    })
  },
  onError: (error) => {
    console.error('Error running evaluation:', error)
    output.value += `Failed to run evaluation. Check console for details.\n`
  },
})

// Update evaluation status when queries change
watch(
  [
    () => agentTraceQuery.data.value,
    () => evalCasesQuery.data.value,
    () => evalResultsQuery.data.value,
  ],
  ([traceExists, casesExist, resultsExist]) => {
    log('Query results updated:', { traceExists, casesExist, resultsExist })

    evaluationStatus.value = {
      hasAgentTrace: !!traceExists,
      hasEvalCases: !!casesExist,
      hasEvalResults: !!resultsExist,
    }

    // Emit status change to parent
    emit('evaluation-status-changed', evaluationStatus.value)
  },
)

// Initial check on component mount
onMounted(() => {
  log('Component mounted with workflow path:', props.workflowPath)
  // Queries are automatically run due to their setup
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
}

.view-results-button {
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  background-color: var(--color-primary, #3b82f6);
  color: white;
  border: none;
  font-weight: 500;
  cursor: pointer;
}

.view-results-button:hover {
  background-color: var(--color-primary-dark, #2563eb);
}

.evaluation-steps {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.eval-button {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: none;
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
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background-color: var(--color-background-soft);
  font-weight: bold;
}

.step-content {
  flex: 1;
}

.step-content h4 {
  margin: 0 0 0.25rem;
}

.step-content p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-light);
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
}

.evaluation-output {
  margin-top: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
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
}

.clear-button {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  cursor: pointer;
}

.clear-button:hover {
  background-color: var(--color-background-mute);
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
}
</style>
