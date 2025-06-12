<!-- filepath: /Users/khaled/github/agent-factory/ui/src/components/AgentTraceViewer.vue -->
<template>
  <div class="agent-trace-viewer">
    <div v-if="loading" class="trace-loading">Loading agent trace...</div>
    <div v-else-if="error" class="trace-error">{{ error }}</div>
    <div v-else-if="!trace" class="trace-empty">No agent trace data available</div>

    <div v-else class="trace-content">
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
            <span class="stat-value">{{ trace.spans.length }}</span>
          </div>
        </div>
        <div class="final-output">
          <h4>Final Output</h4>
          <pre>{{ trace.final_output }}</pre>
        </div>
      </div>

      <!-- Execution Timeline -->
      <div class="execution-timeline">
        <h3>Execution Timeline</h3>
        <div class="timeline">
          <div
            v-for="(span, index) in trace.spans"
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
                      >${{ (span.attributes['gen_ai.usage.input_cost'] || 0).toFixed(6) }}</span
                    >
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">Output Cost</span>
                    <span class="metric-value"
                      >${{ (span.attributes['gen_ai.usage.output_cost'] || 0).toFixed(6) }}</span
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// Props
const props = defineProps<{
  workflowPath: string
}>()

// State
const trace = ref<any>(null)
const loading = ref(true)
const error = ref('')
const expandedSpans = ref<Record<number, boolean>>({})

// Toggle span expansion
function toggleSpan(index: number) {
  expandedSpans.value = {
    ...expandedSpans.value,
    [index]: !expandedSpans.value[index],
  }
}

// Format span title
function formatSpanTitle(name: string): string {
  return name
    .replace('call_llm ', 'LLM Call: ')
    .replace('execute_tool ', 'Tool: ')
    .replace('invoke_agent', 'Agent Execution')
}

// Format duration
function formatDuration(nanoseconds: number): string {
  return (nanoseconds / 1_000_000_000).toFixed(2)
}

// Format time
function formatTime(start: number, end: number): string {
  const durationMs = (end - start) / 1_000_000
  return `${durationMs.toFixed(0)}ms`
}

// Format JSON messages
function formatMessages(messagesJson: string): string {
  try {
    const messages = JSON.parse(messagesJson)
    let formatted = ''

    messages.forEach((msg: any, index: number) => {
      formatted += `[${msg.role}]:\n${msg.content}\n\n`
    })

    return formatted
  } catch (e) {
    return messagesJson
  }
}

// Format JSON output
function formatOutput(outputJson: string): string {
  try {
    const output = JSON.parse(outputJson)
    return JSON.stringify(output, null, 2)
  } catch (e) {
    return outputJson
  }
}

// Format JSON
function formatJson(jsonString: string): string {
  try {
    const obj = JSON.parse(jsonString)
    return JSON.stringify(obj, null, 2)
  } catch (e) {
    return jsonString
  }
}

// Check if span has token info
function hasTokenInfo(span: any): boolean {
  return !!(
    span.attributes['gen_ai.usage.input_tokens'] ||
    span.attributes['gen_ai.usage.output_tokens'] ||
    span.attributes['gen_ai.usage.input_cost'] ||
    span.attributes['gen_ai.usage.output_cost']
  )
}

// Computed properties
const executionDuration = computed(() => {
  if (!trace.value) return 0
  const firstSpan = trace.value.spans.reduce(
    (earliest: any, span: any) =>
      !earliest || span.start_time < earliest.start_time ? span : earliest,
    null,
  )
  const lastSpan = trace.value.spans.reduce(
    (latest: any, span: any) => (!latest || span.end_time > latest.end_time ? span : latest),
    null,
  )

  return firstSpan && lastSpan ? lastSpan.end_time - firstSpan.start_time : 0
})

const totalCost = computed(() => {
  if (!trace.value) return 0
  return trace.value.spans.reduce((sum: number, span: any) => {
    const inputCost = span.attributes['gen_ai.usage.input_cost'] || 0
    const outputCost = span.attributes['gen_ai.usage.output_cost'] || 0
    return sum + inputCost + outputCost
  }, 0)
})

const totalTokens = computed(() => {
  if (!trace.value) return 0
  return trace.value.spans.reduce((sum: number, span: any) => {
    const inputTokens = span.attributes['gen_ai.usage.input_tokens'] || 0
    const outputTokens = span.attributes['gen_ai.usage.output_tokens'] || 0
    return sum + inputTokens + outputTokens
  }, 0)
})

// Load trace data
onMounted(async () => {
  try {
    loading.value = true
    const response = await fetch(
      `http://localhost:3000/agent-factory/workflows/${props.workflowPath}/agent_eval_trace.json`,
    )

    if (!response.ok) {
      throw new Error(`Failed to load agent trace: ${response.status} ${response.statusText}`)
    }

    trace.value = await response.json()

    // Auto-expand the invoke_agent span to show the final result
    const invokeIndex = trace.value.spans.findIndex(
      (s: any) => s.name === 'invoke_agent [any_agent]',
    )
    if (invokeIndex >= 0) {
      expandedSpans.value[invokeIndex] = true
    }
  } catch (err) {
    console.error('Error loading agent trace:', err)
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.agent-trace-viewer {
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
