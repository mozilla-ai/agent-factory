<template>
  <div class="agent-eval-trace-viewer">
    <div v-if="traceQuery.isPending.value" class="trace-loading">
      Loading agent evaluation trace...
    </div>

    <div v-else-if="traceQuery.isError.value" class="trace-error">
      Failed to load agent evaluation trace
    </div>

    <div v-else class="trace-content">
      <div class="trace-header">
        <h3>Agent Evaluation Trace</h3>
        <button class="delete-button" @click="openDeleteDialog">Delete Trace</button>
      </div>

      <!-- Summary Card -->
      <div class="summary-card">
        <h3>Agent Execution Summary</h3>
        <div class="summary-stats">
          <div class="stat">
            <span class="stat-label">Duration</span>
            <span class="stat-value">{{ formatDuration(executionDuration) }} seconds</span>
          </div>
          <div class="stat">
            <span class="stat-label">Total Cost</span>
            <span class="stat-value">${{ totalCost.toFixed(4) }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Total Tokens</span>
            <span class="stat-value">{{ totalTokens }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Steps</span>
            <span class="stat-value">{{ traceQuery.data.value.spans.length }}</span>
          </div>
        </div>
        <div class="final-output">
          <h4>Final Output</h4>
          <pre>{{ traceQuery.data.value.final_output }}</pre>
        </div>
      </div>

      <!-- Execution Timeline -->
      <div class="execution-timeline">
        <h3>Execution Timeline</h3>
        <div class="timeline">
          <div
            v-for="(span, index) in traceQuery.data.value.spans"
            :key="index"
            class="timeline-item"
            :class="{
              'timeline-item-llm': span.name.startsWith('call_llm'),
              'timeline-item-tool': span.name.startsWith('execute_tool'),
            }"
          >
            <div class="timeline-header" @click="toggleSpan(index)">
              <div class="timeline-icon">
                <span v-if="span.name.startsWith('call_llm')">🤖</span>
                <span v-else-if="span.name.startsWith('execute_tool')">🔧</span>
                <span v-else>📝</span>
              </div>
              <div class="timeline-title">
                <h4>{{ formatSpanTitle(span.name) }}</h4>
                <span class="timeline-time">{{ formatTime(span.start_time, span.end_time) }}</span>
              </div>
              <div class="timeline-expand">
                <span v-if="expandedSpans[index]">▼</span>
                <span v-else>►</span>
              </div>
            </div>

            <div class="timeline-details" v-if="expandedSpans[index]">
              <div v-if="span.attributes['gen_ai.input.messages']" class="detail-section">
                <h5>Input</h5>
                <pre class="trace-code">{{
                  formatMessages(span.attributes['gen_ai.input.messages'])
                }}</pre>
              </div>

              <div v-if="span.attributes['gen_ai.output']" class="detail-section">
                <h5>Output</h5>
                <pre class="trace-code">{{ formatOutput(span.attributes['gen_ai.output']) }}</pre>
              </div>

              <div v-if="span.attributes['gen_ai.tool.args']" class="detail-section">
                <h5>Tool Arguments</h5>
                <pre class="trace-code">{{ formatJson(span.attributes['gen_ai.tool.args']) }}</pre>
              </div>

              <div v-if="hasTokenInfo(span)" class="detail-section metrics">
                <h5>Metrics</h5>
                <div class="metrics-grid">
                  <div class="metric-item">
                    <span class="metric-label">Input Tokens</span>
                    <span class="metric-value">{{
                      span.attributes['gen_ai.usage.input_tokens'] || 'N/A'
                    }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">Output Tokens</span>
                    <span class="metric-value">{{
                      span.attributes['gen_ai.usage.output_tokens'] || 'N/A'
                    }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">Input Cost</span>
                    <span class="metric-value"
                      >${{
                        Number(span.attributes['gen_ai.usage.input_cost'] || 0).toFixed(6)
                      }}</span
                    >
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">Output Cost</span>
                    <span class="metric-value"
                      >${{
                        Number(span.attributes['gen_ai.usage.output_cost'] || 0).toFixed(6)
                      }}</span
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Confirmation Dialog -->
    <ConfirmationDialog
      :isOpen="showDeleteDialog"
      title="Delete Agent Evaluation Trace"
      message="Are you sure you want to delete this agent evaluation trace? This will also delete any evaluation results. This action cannot be undone."
      confirmButtonText="Delete"
      :isDangerous="true"
      :isLoading="deleteTraceMutation.isPending.value"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { deleteAgentEvalTrace } from '../../services/evaluationService'
import ConfirmationDialog from '../ConfirmationDialog.vue'
import { workflowService } from '@/services/workflowService'
import { useRouter } from 'vue-router'

interface TraceMessage {
  role: string
  content: string
}

// interface AgentTrace {
//   spans: TraceSpan[]
//   final_output: string
// }

// Update the TraceSpan interface to properly type the attributes
interface TraceSpan {
  name: string
  kind: string
  parent: Record<string, unknown>
  start_time: number
  end_time: number
  status: {
    status_code: string
    description: string | null
  }
  context: Record<string, unknown>
  attributes: {
    'gen_ai.input.messages'?: string
    'gen_ai.output'?: string
    'gen_ai.tool.args'?: string
    'gen_ai.usage.input_tokens'?: number
    'gen_ai.usage.output_tokens'?: number
    'gen_ai.usage.input_cost'?: number
    'gen_ai.usage.output_cost'?: number
    [key: string]: unknown
  }
  links: unknown[]
  events: unknown[]
  resource: {
    attributes: Record<string, string>
    schema_url: string
  }
}

// Props
const props = defineProps<{
  workflowPath: string
}>()

// State for UI interactions
const expandedSpans = ref<Record<number, boolean>>({})
const showDeleteDialog = ref(false)
const queryClient = useQueryClient()

// Fetch agent trace data using TanStack Query
const traceQuery = useQuery({
  queryKey: ['agentEvalTrace', props.workflowPath],
  queryFn: () => workflowService.getAgentTrace(props.workflowPath),
  retry: 1,
})
const router = useRouter()

// Delete mutation
const deleteTraceMutation = useMutation({
  mutationFn: () => deleteAgentEvalTrace(props.workflowPath),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['agentEvalTrace', props.workflowPath] })
    queryClient.invalidateQueries({ queryKey: ['evaluation-status', props.workflowPath] })
    queryClient.invalidateQueries({ queryKey: ['evaluation-results', props.workflowPath] })
    showDeleteDialog.value = false
    router.push({
      params: { workflowPath: props.workflowPath },
      query: { tab: 'evaluate' },
    })
  },
})

// Toggle span expansion
function toggleSpan(index: number): void {
  expandedSpans.value = {
    ...expandedSpans.value,
    [index]: !expandedSpans.value[index],
  }
}

// Format span title for display
function formatSpanTitle(name: string): string {
  return name
    .replace('call_llm ', 'LLM Call: ')
    .replace('execute_tool ', 'Tool: ')
    .replace('invoke_agent', 'Agent Execution')
}

// Format duration for display
function formatDuration(nanoseconds: number): string {
  return (nanoseconds / 1_000_000_000).toFixed(2)
}

// Format time for display
function formatTime(start: number, end: number): string {
  const durationMs = (end - start) / 1_000_000
  return `${durationMs.toFixed(0)}ms`
}

// Format JSON messages for display
function formatMessages(messagesJson: unknown): string {
  if (typeof messagesJson !== 'string') return String(messagesJson || '')

  try {
    const messages = JSON.parse(messagesJson) as TraceMessage[]
    let formatted = ''

    messages.forEach((msg: TraceMessage) => {
      formatted += `[${msg.role}]:\n${msg.content}\n\n`
    })

    return formatted
  } catch {
    return String(messagesJson)
  }
}

// Format JSON output for display
function formatOutput(outputJson: unknown): string {
  if (typeof outputJson !== 'string') return String(outputJson || '')

  try {
    const output = JSON.parse(outputJson) as Record<string, unknown>
    return JSON.stringify(output, null, 2)
  } catch {
    return String(outputJson)
  }
}

// Format JSON for display
function formatJson(jsonString: unknown): string {
  if (typeof jsonString !== 'string') return String(jsonString || '')

  try {
    const obj = JSON.parse(jsonString) as Record<string, unknown>
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(jsonString)
  }
}

// Check if span has token info
function hasTokenInfo(span: TraceSpan): boolean {
  return !!(
    span.attributes['gen_ai.usage.input_tokens'] ||
    span.attributes['gen_ai.usage.output_tokens'] ||
    span.attributes['gen_ai.usage.input_cost'] ||
    span.attributes['gen_ai.usage.output_cost']
  )
}

// Calculate execution duration
const executionDuration = computed(() => {
  if (!traceQuery.data.value) return 0

  const firstSpan = traceQuery.data.value.spans.reduce(
    (earliest: TraceSpan | null, span: TraceSpan) =>
      !earliest || span.start_time < earliest.start_time ? span : earliest,
    null,
  )

  const lastSpan = traceQuery.data.value.spans.reduce(
    (latest: TraceSpan | null, span: TraceSpan) =>
      !latest || span.end_time > latest.end_time ? span : latest,
    null,
  )

  return firstSpan && lastSpan ? lastSpan.end_time - firstSpan.start_time : 0
})

// Calculate total cost
const totalCost = computed(() => {
  if (!traceQuery.data.value) return 0

  return traceQuery.data.value.spans.reduce((sum: number, span: TraceSpan) => {
    const inputCost = Number(span.attributes['gen_ai.usage.input_cost']) || 0
    const outputCost = Number(span.attributes['gen_ai.usage.output_cost']) || 0
    return sum + inputCost + outputCost
  }, 0)
})

// Calculate total tokens
const totalTokens = computed(() => {
  if (!traceQuery.data.value) return 0

  return traceQuery.data.value.spans.reduce((sum: number, span: TraceSpan) => {
    const inputTokens = Number(span.attributes['gen_ai.usage.input_tokens']) || 0
    const outputTokens = Number(span.attributes['gen_ai.usage.output_tokens']) || 0
    return sum + inputTokens + outputTokens
  }, 0)
})

// Functions for delete confirmation
const openDeleteDialog = () => {
  showDeleteDialog.value = true
}

const confirmDelete = () => {
  deleteTraceMutation.mutate()
}

const cancelDelete = () => {
  showDeleteDialog.value = false
}
</script>

<style scoped>
.agent-eval-trace-viewer {
  padding: 1rem;
}

.trace-loading,
.trace-error,
.trace-empty {
  text-align: center;
  padding: 2rem;
  font-size: 1.1rem;
}

.trace-error {
  color: var(--color-error, #e74c3c);
}

.summary-card {
  background-color: var(--color-background-soft);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin: 1rem 0;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--color-text-light, var(--color-text-secondary));
}

.stat-value {
  font-size: 1.2rem;
  font-weight: 500;
}

.final-output {
  background-color: var(--color-background);
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1rem;
  border: 1px solid var(--color-border);
}

.final-output pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.timeline-item {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.timeline-item-llm {
  border-left: 4px solid #3498db;
}

.timeline-item-tool {
  border-left: 4px solid #2ecc71;
}

.timeline-header {
  display: flex;
  padding: 1rem;
  cursor: pointer;
  background-color: var(--color-background);
  align-items: center;
  gap: 0.5rem;
}

.timeline-header:hover {
  background-color: var(--color-background-soft);
}

.timeline-icon {
  font-size: 1.5rem;
  width: 2rem;
  text-align: center;
}

.timeline-title {
  flex: 1;
}

.timeline-title h4 {
  margin: 0;
  font-weight: 500;
}

.timeline-time {
  font-size: 0.9rem;
  color: var(--color-text-light, var(--color-text-secondary));
}

.timeline-details {
  padding: 1rem;
  background-color: var(--color-background-soft);
  border-top: 1px solid var(--color-border);
}

.detail-section {
  margin-bottom: 1rem;
}

.detail-section h5 {
  margin: 0 0 0.5rem 0;
  font-weight: 500;
  color: var(--color-heading, var(--color-text));
}

.trace-code {
  background-color: var(--color-background);
  padding: 0.75rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9rem;
  overflow: auto;
  max-height: 300px;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  border: 1px solid var(--color-border);
}

.metrics {
  background-color: var(--color-background);
  border-radius: 4px;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}

.metric-item {
  display: flex;
  flex-direction: column;
}

.metric-label {
  font-size: 0.8rem;
  color: var(--color-text-light, var(--color-text-secondary));
}

.metric-value {
  font-weight: 500;
}

.agent-eval-trace-viewer {
  padding: 1rem;
}

.trace-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.delete-button {
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  border: 1px solid var(--color-error);
  background-color: var(--color-error-soft);
  color: var(--color-error);
  font-weight: 500;
  cursor: pointer;
}

.delete-button:hover {
  background-color: var(--color-error);
  color: white;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .summary-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .summary-stats,
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
