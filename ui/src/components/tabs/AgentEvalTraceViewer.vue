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
        <BaseButton variant="danger" @click="handleDeleteClick">Delete Trace</BaseButton>
      </div>

      <!-- Summary Card -->
      <div class="summary-card">
        <h3>Agent Execution Summary</h3>
        <div class="summary-stats">
          <MetricDisplay label="Duration" :value="`${formatDuration(executionDuration)} seconds`" />
          <MetricDisplay label="Total Cost" :value="`$${totalCost.toFixed(4)}`" />
          <MetricDisplay label="Total Tokens" :value="totalTokens" />
          <MetricDisplay label="Steps" :value="traceQuery.data.value?.spans?.length || 0" />
        </div>
        <div class="final-output">
          <h4>Final Output</h4>
          <pre>{{ JSON.stringify(traceQuery.data.value?.final_output, null, 2) }}</pre>
        </div>
      </div>

      <!-- Execution Timeline -->
      <div class="execution-timeline">
        <h3>Execution Timeline</h3>
        <div class="timeline">
          <TimelineItem
            v-for="(span, index) in traceQuery.data.value?.spans || []"
            :key="index"
            :title="formatSpanTitle(span.name)"
            :duration="formatTime(span.start_time, span.end_time)"
            :is-expanded="!!expandedSpans[index]"
            :is-l-l-m-call="span.name.startsWith('call_llm')"
            :is-tool-call="span.name.startsWith('execute_tool')"
            @toggle="toggleSpan(index)"
          >
            <TraceSection v-if="span.attributes['gen_ai.input.messages']" title="Input">
              <CodeBlock :content="safeJsonFormat(span.attributes['gen_ai.input.messages'])" />
            </TraceSection>

            <TraceSection v-if="span.attributes['gen_ai.output']" title="Output">
              <CodeBlock :content="safeJsonFormat(span.attributes['gen_ai.output'])" />
            </TraceSection>

            <TraceSection v-if="span.attributes['gen_ai.tool.args']" title="Tool Arguments">
              <CodeBlock :content="safeJsonFormat(span.attributes['gen_ai.tool.args'])" />
            </TraceSection>

            <TraceSection v-if="hasTokenInfo(span)" title="Metrics" variant="metrics">
              <MetricDisplay
                variant="metric"
                label="Input Tokens"
                :value="span.attributes['gen_ai.usage.input_tokens'] || 'N/A'"
              />
              <MetricDisplay
                variant="metric"
                label="Output Tokens"
                :value="span.attributes['gen_ai.usage.output_tokens'] || 'N/A'"
              />
              <MetricDisplay
                variant="metric"
                label="Input Cost"
                :value="`$${Number(span.attributes['gen_ai.usage.input_cost'] || 0).toFixed(6)}`"
              />
              <MetricDisplay
                variant="metric"
                label="Output Cost"
                :value="`$${Number(span.attributes['gen_ai.usage.output_cost'] || 0).toFixed(6)}`"
              />
            </TraceSection>

            <!-- Fallback: Show all attributes if no standard ones are found -->
            <TraceSection
              v-if="!hasStandardAttributes(span) && Object.keys(span.attributes).length > 0"
              title="Span Attributes"
            >
              <CodeBlock :content="safeJsonFormat(JSON.stringify(span.attributes, null, 2))" />
            </TraceSection>

            <!-- If no attributes at all, show a message -->
            <TraceSection v-if="Object.keys(span.attributes).length === 0">
              <p class="no-details">No detailed information available for this step.</p>
            </TraceSection>
          </TimelineItem>
        </div>
      </div>
    </div>

    <!-- Add Confirmation Dialog -->
    <ConfirmationDialog
      :isOpen="showDeleteDialog"
      :title="deleteOptions?.title || 'Delete Agent Evaluation Trace'"
      :message="
        deleteOptions?.message || 'Are you sure you want to delete this agent evaluation trace?'
      "
      :confirmButtonText="deleteOptions?.confirmButtonText || 'Delete'"
      :isDangerous="true"
      :isLoading="deleteTraceMutation.isPending.value"
      @confirm="confirmDelete"
      @cancel="closeDeleteDialog"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { evaluationService } from '../../services/evaluationService'
import ConfirmationDialog from '../ConfirmationDialog.vue'
import { workflowService } from '@/services/workflowService'
import { useRouter } from 'vue-router'
import { useWorkflowsStore } from '@/stores/workflows'
import { useDeleteConfirmation } from '@/composables/useDeleteConfirmation'
import MetricDisplay from '../MetricDisplay.vue'
import TraceSection from '../TraceSection.vue'
import CodeBlock from '../CodeBlock.vue'
import TimelineItem from '../TimelineItem.vue'
import BaseButton from '../BaseButton.vue'

const workflowsStore = useWorkflowsStore()

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
  workflowId: string
}>()

// State for UI interactions
const expandedSpans = ref<Record<number, boolean>>({})
const queryClient = useQueryClient()

// Use delete confirmation composable
const { showDeleteDialog, deleteOptions, openDeleteDialog, closeDeleteDialog } =
  useDeleteConfirmation()

// Fetch agent trace data using TanStack Query
const traceQuery = useQuery({
  queryKey: ['agentEvalTrace', props.workflowId],
  queryFn: () => workflowService.getAgentTrace(props.workflowId),
  retry: 1,
})
const router = useRouter()

// Delete mutation
const deleteTraceMutation = useMutation({
  mutationFn: () => evaluationService.deleteAgentEvalTrace(props.workflowId),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['agentEvalTrace', props.workflowId] })
    queryClient.invalidateQueries({ queryKey: ['evaluation-status', props.workflowId] })
    queryClient.invalidateQueries({ queryKey: ['evaluation-results', props.workflowId] })
    // Refresh the workflow store to update file explorer
    workflowsStore.loadWorkflows()
    queryClient.invalidateQueries({
      queryKey: ['file-content', props.workflowId, 'agent_eval_trace.json'],
    })
    closeDeleteDialog()
    router.push({
      params: { workflowId: props.workflowId },
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

// Check if span has token info
function hasTokenInfo(span: TraceSpan): boolean {
  return !!(
    span.attributes['gen_ai.usage.input_tokens'] ||
    span.attributes['gen_ai.usage.output_tokens'] ||
    span.attributes['gen_ai.usage.input_cost'] ||
    span.attributes['gen_ai.usage.output_cost']
  )
}

// Check if span has standard attributes that we specifically handle
function hasStandardAttributes(span: TraceSpan): boolean {
  return !!(
    span.attributes['gen_ai.input.messages'] ||
    span.attributes['gen_ai.output'] ||
    span.attributes['gen_ai.tool.args'] ||
    hasTokenInfo(span)
  )
}

// Safely format JSON or return as-is if it's not valid JSON
function safeJsonFormat(value: unknown): string {
  if (!value) return ''

  const stringValue = String(value)

  // Try to parse as JSON first
  try {
    const parsed = JSON.parse(stringValue)
    return JSON.stringify(parsed, null, 2)
  } catch {
    // If it's not valid JSON, return the raw string
    return stringValue
  }
}

// Calculate execution duration
const executionDuration = computed(() => {
  if (!traceQuery.data.value?.spans) return 0

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
  if (!traceQuery.data.value?.spans) return 0

  return traceQuery.data.value.spans.reduce((sum: number, span: TraceSpan) => {
    const inputCost = Number(span.attributes['gen_ai.usage.input_cost']) || 0
    const outputCost = Number(span.attributes['gen_ai.usage.output_cost']) || 0
    return sum + inputCost + outputCost
  }, 0)
})

// Calculate total tokens
const totalTokens = computed(() => {
  if (!traceQuery.data.value?.spans) return 0

  return traceQuery.data.value.spans.reduce((sum: number, span: TraceSpan) => {
    const inputTokens = Number(span.attributes['gen_ai.usage.input_tokens']) || 0
    const outputTokens = Number(span.attributes['gen_ai.usage.output_tokens']) || 0
    return sum + inputTokens + outputTokens
  }, 0)
})

// Functions for delete confirmation
const handleDeleteClick = () => {
  openDeleteDialog({
    title: 'Delete Agent Evaluation Trace',
    message:
      'Are you sure you want to delete this agent evaluation trace? This will also delete any evaluation results. This action cannot be undone.',
    confirmButtonText: 'Delete',
  })
}

const confirmDelete = () => {
  deleteTraceMutation.mutate()
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

.agent-eval-trace-viewer {
  padding: 1rem;
}

.trace-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
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

.no-details {
  color: var(--color-text-light, var(--color-text-secondary));
  font-style: italic;
  margin: 0;
  text-align: center;
  padding: 1rem;
}
</style>
