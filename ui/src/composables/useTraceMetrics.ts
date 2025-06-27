import { computed } from 'vue'
import type { TraceSpan } from '@/types'

/**
 * Composable for calculating agent trace metrics
 * Extracts complex calculations from components
 */
export function useTraceMetrics(traceData: { value?: { spans?: TraceSpan[] } }) {
  // Calculate execution duration
  const executionDuration = computed(() => {
    if (!traceData.value?.spans) return 0

    const spans = traceData.value.spans
    const firstSpan = spans.reduce(
      (earliest: TraceSpan | null, span: TraceSpan) =>
        !earliest || span.start_time < earliest.start_time ? span : earliest,
      null,
    )

    const lastSpan = spans.reduce(
      (latest: TraceSpan | null, span: TraceSpan) =>
        !latest || span.end_time > latest.end_time ? span : latest,
      null,
    )

    return firstSpan && lastSpan ? lastSpan.end_time - firstSpan.start_time : 0
  })

  // Calculate total cost
  const totalCost = computed(() => {
    if (!traceData.value?.spans) return 0

    return traceData.value.spans.reduce((sum: number, span: TraceSpan) => {
      const inputCost = Number(span.attributes['gen_ai.usage.input_cost']) || 0
      const outputCost = Number(span.attributes['gen_ai.usage.output_cost']) || 0
      return sum + inputCost + outputCost
    }, 0)
  })

  // Calculate total tokens
  const totalTokens = computed(() => {
    if (!traceData.value?.spans) return 0

    return traceData.value.spans.reduce((sum: number, span: TraceSpan) => {
      const inputTokens = Number(span.attributes['gen_ai.usage.input_tokens']) || 0
      const outputTokens = Number(span.attributes['gen_ai.usage.output_tokens']) || 0
      return sum + inputTokens + outputTokens
    }, 0)
  })

  // Format helpers
  const formatDuration = (nanoseconds: number): string => {
    return (nanoseconds / 1_000_000_000).toFixed(2)
  }

  const formatTime = (start: number, end: number): string => {
    const durationMs = (end - start) / 1_000_000
    return `${durationMs.toFixed(0)}ms`
  }

  const formatSpanTitle = (name: string): string => {
    return name
      .replace('call_llm ', 'LLM Call: ')
      .replace('execute_tool ', 'Tool: ')
      .replace('invoke_agent', 'Agent Execution')
  }

  // Span analysis helpers
  const hasTokenInfo = (span: TraceSpan): boolean => {
    return !!(
      span.attributes['gen_ai.usage.input_tokens'] ||
      span.attributes['gen_ai.usage.output_tokens'] ||
      span.attributes['gen_ai.usage.input_cost'] ||
      span.attributes['gen_ai.usage.output_cost']
    )
  }

  const hasStandardAttributes = (span: TraceSpan): boolean => {
    return !!(
      span.attributes['gen_ai.input.messages'] ||
      span.attributes['gen_ai.output'] ||
      span.attributes['gen_ai.tool.args'] ||
      hasTokenInfo(span)
    )
  }

  return {
    // Computed metrics
    executionDuration,
    totalCost,
    totalTokens,
    // Formatters
    formatDuration,
    formatTime,
    formatSpanTitle,
    // Helpers
    hasTokenInfo,
    hasStandardAttributes,
  }
}
