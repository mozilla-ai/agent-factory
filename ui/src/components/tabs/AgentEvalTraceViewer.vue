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
      @delete-clicked="handleDelete"
    />

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
import { useQuery, useMutation } from '@tanstack/vue-query'
import { evaluationService } from '../../services/evaluationService'
import ConfirmationDialog from '../ConfirmationDialog.vue'
import { workflowService } from '@/services/workflowService'
import { useDeleteConfirmation } from '@/composables/useDeleteConfirmation'
import { useQueryInvalidation } from '@/composables/useQueryInvalidation'
import { useNavigation } from '@/composables/useNavigation'
import { queryKeys } from '@/helpers/queryKeys'
import AgentTrace from '../AgentTrace.vue'

const {
  invalidateEvaluationQueries,
  invalidateAgentTrace,
  invalidateFileQueries,
  invalidateWorkflows,
} = useQueryInvalidation()
const { navigateToEvaluate } = useNavigation()

// Props
const props = defineProps<{
  workflowId: string
}>()

// Use delete confirmation composable
const { showDeleteDialog, deleteOptions, openDeleteDialog, closeDeleteDialog } =
  useDeleteConfirmation()

// Fetch agent trace data using TanStack Query
const traceQuery = useQuery({
  queryKey: queryKeys.agentTrace(props.workflowId),
  queryFn: () => workflowService.getAgentTrace(props.workflowId),
  retry: 1,
})

// Delete mutation
const deleteTraceMutation = useMutation({
  mutationFn: () => evaluationService.deleteAgentEvalTrace(props.workflowId),
  onSuccess: () => {
    invalidateAgentTrace(props.workflowId)
    invalidateEvaluationQueries(props.workflowId)
    invalidateFileQueries(props.workflowId, 'agent_eval_trace.json', 'evaluation_results.json')
    invalidateWorkflows()
    closeDeleteDialog()
    navigateToEvaluate(props.workflowId)
  },
})
const handleDelete = () => {
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
</style>
