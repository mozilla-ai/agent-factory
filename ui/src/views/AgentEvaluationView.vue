<template>
  <div class="agent-evaluation">
    <h2>Agent Evaluation</h2>

    <div class="workflow-selector">
      <label for="workflow-path">Select Workflow:</label>
      <select id="workflow-path" v-model="selectedWorkflow">
        <option v-for="(workflow, index) in workflows" :key="index" :value="workflow">
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

const selectedWorkflow = ref('')
const workflows = ref<string[]>([])
const output = ref('')
const isRunningAgent = ref(false)
const isGeneratingCases = ref(false)
const isRunningEval = ref(false)
const currentOperation = ref('')

onMounted(async () => {
  try {
    const response = await fetch('http://localhost:3000/agent-factory/workflows')
    if (response.ok) {
      workflows.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to load workflows:', error)
  }
})

// Helper function to handle streaming response
async function handleStreamingResponse(response: Response): Promise<void> {
  const reader = response.body?.getReader()
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

    const response = await fetch(
      `http://localhost:3000/agent-factory/evaluate/run-agent/${selectedWorkflow.value}`,
      { method: 'POST' },
    )

    await handleStreamingResponse(response)
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

    const response = await fetch(
      `http://localhost:3000/agent-factory/evaluate/generate-cases/${selectedWorkflow.value}`,
      {
        method: 'POST',
      },
    )

    await handleStreamingResponse(response)
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

    const response = await fetch(
      `http://localhost:3000/agent-factory/evaluate/run-evaluation/${selectedWorkflow.value}`,
      { method: 'POST' },
    )

    await handleStreamingResponse(response)
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
