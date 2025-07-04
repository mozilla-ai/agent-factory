<template>
  <div class="trace-content">
    <div class="trace-header">
      <h3>Agent Evaluation Trace</h3>
      <BaseButton v-if="showActions" variant="danger" @click="handleDeleteClick"
        >Delete Trace</BaseButton
      >
    </div>

    <!-- Summary Card -->
    <div class="summary-card">
      <h3>Agent Execution Summary</h3>
      <div class="summary-stats">
        <MetricDisplay label="Duration" :value="`${formatDuration(executionDuration)} seconds`" />
        <MetricDisplay label="Total Cost" :value="`$${totalCost}`" />
        <MetricDisplay label="Total Tokens" :value="totalTokens" />
        <MetricDisplay label="Steps" :value="agentTrace.spans?.length || 0" />
      </div>
      <div class="final-output">
        <h4>Final Output</h4>
        <pre>{{ JSON.stringify(agentTrace.final_output, null, 2) }}</pre>
      </div>
    </div>

    <!-- Execution Timeline -->
    <div class="execution-timeline">
      <h3>Execution Timeline</h3>
      <div class="timeline">
        <TimelineItem
          v-for="(span, index) in agentTrace.spans || []"
          :key="index"
          :title="formatSpanTitle(span.name)"
          :duration="formatTime(span.start_time, span.end_time)"
          :is-expanded="!!expandedSpans[index]"
          :is-l-l-m-call="span.name.startsWith('call_llm')"
          :is-tool-call="span.name.startsWith('execute_tool')"
          :is-agent-execution="span.name.startsWith('invoke_agent')"
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
</template>

<script setup lang="ts">
import type { AgentTrace } from '@/types'
import MetricDisplay from './MetricDisplay.vue'
import TraceSection from './TraceSection.vue'
import CodeBlock from './CodeBlock.vue'
import TimelineItem from './TimelineItem.vue'
import BaseButton from './BaseButton.vue'
import { useTraceMetrics } from '@/composables/useTraceMetrics'
import { ref } from 'vue'

const props = withDefaults(
  defineProps<{
    agentTrace: AgentTrace
    showActions?: boolean
  }>(),
  {
    showActions: true,
  },
)

const emit = defineEmits<{
  (e: 'delete-clicked'): void
}>()

// State for UI interactions
const expandedSpans = ref<Record<number, boolean>>({})

// Use trace metrics composable for calculations
const {
  executionDuration,
  totalCost,
  totalTokens,
  formatDuration,
  formatTime,
  formatSpanTitle,
  hasTokenInfo,
  hasStandardAttributes,
} = useTraceMetrics(props.agentTrace)

function toggleSpan(index: number): void {
  expandedSpans.value = {
    ...expandedSpans.value,
    [index]: !expandedSpans.value[index],
  }
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

// Functions for delete confirmation
const handleDeleteClick = () => {
  emit('delete-clicked')
}
</script>

<style scoped>
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
