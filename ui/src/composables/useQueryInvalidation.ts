import { useQueryClient } from '@tanstack/vue-query'
import { queryKeys } from '@/helpers/queryKeys'
import { useWorkflows } from './useWorkflows'

export function useQueryInvalidation() {
  const queryClient = useQueryClient()
  const { invalidateWorkflows } = useWorkflows()

  const invalidateEvaluationQueries = (workflowId: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.evaluationCriteria(workflowId) })
    queryClient.invalidateQueries({ queryKey: queryKeys.evaluationResults(workflowId) })
    queryClient.invalidateQueries({ queryKey: queryKeys.evaluationStatus(workflowId) })
  }

  const invalidateFileQueries = (workflowId: string, ...fileNames: string[]) => {
    fileNames.forEach((fileName) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.fileContent(workflowId, fileName),
      })
    })
  }

  const invalidateAgentTrace = (workflowId: string) => {
    queryClient.invalidateQueries({ queryKey: queryKeys.agentTrace(workflowId) })
  }

  const invalidateAllForWorkflow = (workflowId: string) => {
    invalidateEvaluationQueries(workflowId)
    invalidateAgentTrace(workflowId)
    invalidateFileQueries(
      workflowId,
      'evaluation_case.yaml',
      'evaluation_results.json',
      'agent_eval_trace.json',
    )
    invalidateWorkflows()
  }

  return {
    invalidateEvaluationQueries,
    invalidateFileQueries,
    invalidateAgentTrace,
    invalidateAllForWorkflow,
    invalidateWorkflows,
  }
}
