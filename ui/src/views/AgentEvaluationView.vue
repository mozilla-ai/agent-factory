<template>
  <div class="agent-evaluation">
    <h2>Agent Evaluation</h2>

    <div class="workflow-selector">
      <label for="workflow-id">Select Workflow:</label>
      <select id="workflow-id" v-model="selectedWorkflow">
        <option
          v-for="(workflow, index) in workflowStore.workflows.map((w) => w.name)"
          :key="index"
          :value="workflow"
        >
          {{ workflow }}
        </option>
      </select>
    </div>

    <div class="evaluation-actions">
      <button
        @click="runAgent"
        :disabled="isRunningAgent || isGeneratingCases || isRunningEval"
        class="eval-button"
      >
        1. Run Agent
      </button>

      <button
        @click="generateEvaluationCases"
        :disabled="isRunningAgent || isGeneratingCases || isRunningEval"
        class="eval-button"
      >
        2. Generate Evaluation Cases
      </button>

      <button
        @click="runEvaluation"
        :disabled="isRunningAgent || isGeneratingCases || isRunningEval"
        class="eval-button"
      >
        3. Run Evaluation
      </button>
    </div>

    <div class="evaluation-output">
      <h3>Output</h3>
      <div v-if="isRunningAgent || isGeneratingCases || isRunningEval" class="loading">
        {{ currentOperation }} in progress...
      </div>

      <pre v-if="output" class="output-content">{{ output }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useWorkflowsStore } from '@/stores/workflows'
import { evaluationService } from '@/services/evaluationService'

const selectedWorkflow = ref('')
const output = ref('')
const isRunningAgent = ref(false)
const isGeneratingCases = ref(false)
const isRunningEval = ref(false)
const currentOperation = ref('')
const workflowStore = useWorkflowsStore()

onMounted(() => {
  console.log('AgentEvaluationView mounted')
  workflowStore.loadWorkflows()
})

// Helper function to handle streaming response
async function handleStreamingResponse(body: ReadableStream): Promise<void> {
  const reader = body?.getReader()
  if (!reader) {
    output.value += 'Error: No response body'
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

// Run agent
async function runAgent() {
  try {
    isRunningAgent.value = true
    currentOperation.value = 'Running agent'
    output.value = ''

    const body = await evaluationService.runAgent(selectedWorkflow.value)

    await handleStreamingResponse(body)
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    output.value += '\nError: ' + errorMessage
  } finally {
    isRunningAgent.value = false
    currentOperation.value = ''
  }
}

// Generate evaluation cases
async function generateEvaluationCases() {
  try {
    isGeneratingCases.value = true
    currentOperation.value = 'Generating evaluation cases'
    output.value = ''

    const body = await evaluationService.generateEvaluationCases(selectedWorkflow.value)

    await handleStreamingResponse(body)
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    output.value += '\nError: ' + errorMessage
  } finally {
    isGeneratingCases.value = false
    currentOperation.value = ''
  }
}

// Run evaluation
async function runEvaluation() {
  try {
    isRunningEval.value = true
    currentOperation.value = 'Running evaluation'
    output.value = ''

    const body = await evaluationService.runEvaluation(selectedWorkflow.value)

    await handleStreamingResponse(body)
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    output.value += '\nError: ' + errorMessage
  } finally {
    isRunningEval.value = false
    currentOperation.value = ''
  }
}
</script>

<style scoped>
.agent-evaluation {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  max-width: 100%;
}

.workflow-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.workflow-selector select {
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
}

.evaluation-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.eval-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.25rem;
  border-radius: 4px;
  background: var(--color-background-soft);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}

.eval-button:hover:not(:disabled) {
  background: var(--color-background-mute);
  border-color: var(--color-border-hover);
}

.eval-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.evaluation-output {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.output-content {
  display: flex;
  flex-direction: column;
  background: var(--color-background-soft);
  padding: 1rem;
  border-radius: 4px;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
}

.loading {
  display: flex;
  padding: 1rem;
  font-style: italic;
  color: var(--color-text-light);
}
</style>
