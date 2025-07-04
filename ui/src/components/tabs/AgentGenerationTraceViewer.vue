<template>
  <div class="agent-eval-trace-viewer">
    <div v-if="traceQuery.isPending.value" class="trace-loading">
      Loading agent evaluation trace...
    </div>

    <div v-else-if="traceQuery.isError.value" class="trace-error">
      Failed to load agent evaluation trace
    </div>

    <AgentTrace
      v-if="traceQuery.data.value"
      :agent-trace="traceQuery.data.value"
      :show-actions="false"
    />
  </div>
</template>

<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { workflowService } from '@/services/workflowService'

import { queryKeys } from '@/helpers/queryKeys'
import AgentTrace from '../AgentTrace.vue'

// Props
const props = defineProps<{
  workflowId: string
}>()

// Fetch agent trace data using TanStack Query
const traceQuery = useQuery({
  queryKey: queryKeys.agentTrace(props.workflowId),
  queryFn: () => workflowService.getAgentGenerationTrace(props.workflowId),
  retry: 1,
})
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
</style>
