/**
 * Centralized query key factory for TanStack Query
 * Ensures consistent cache keys and easier cache invalidation
 */

export const queryKeys = {
  // Workflow-related queries
  workflows: () => ['workflows'] as const,
  workflow: (id: string) => ['workflow', id] as const,
  workflowFiles: (id: string) => ['workflow', id, 'files'] as const,
  fileContent: (workflowId: string, fileName: string) =>
    ['file-content', workflowId, fileName] as const,

  // Evaluation-related queries
  evaluationStatus: (workflowId: string) => ['evaluation-status', workflowId] as const,
  evaluationCriteria: (workflowId: string) => ['evaluation-criteria', workflowId] as const,
  evaluationResults: (workflowId: string) => ['evaluation-results', workflowId] as const,
  agentTrace: (workflowId: string) => ['agentEvalTrace', workflowId] as const,
} as const

/**
 * Helper to invalidate all evaluation-related queries for a workflow
 */
export function getEvaluationQueryKeys(workflowId: string) {
  return [
    queryKeys.evaluationStatus(workflowId),
    queryKeys.evaluationCriteria(workflowId),
    queryKeys.evaluationResults(workflowId),
    queryKeys.agentTrace(workflowId),
  ]
}

/**
 * Helper to invalidate all file-related queries for a workflow
 */
export function getFileQueryKeys(workflowId: string) {
  return [
    queryKeys.workflowFiles(workflowId),
    // Pattern to match all file content queries for this workflow
    { queryKey: ['file-content', workflowId] },
  ]
}
