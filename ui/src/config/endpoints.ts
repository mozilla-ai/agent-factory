/**
 * All API endpoints in one place for easy migration
 */

export const ENDPOINTS = {
  // Health check
  health: 'health',

  // Workflows
  workflows: 'api/workflows',
  workflowDetails: (workflowId: string) => `api/workflows/${encodeURIComponent(workflowId)}`,
  workflowFile: (workflowId: string, filePath: string) =>
    `workflows/${encodeURIComponent(workflowId)}/${filePath}`,
  workflowCriteria: (workflowId: string) =>
    `api/workflows/${encodeURIComponent(workflowId)}/criteria`,
  workflowResults: (workflowId: string) =>
    `api/workflows/${encodeURIComponent(workflowId)}/results`,

  // Agent generation and management
  generateAgent: 'api/agent/generate',
  sendInput: 'api/agent/input',
  stopAgent: 'api/agent/stop',

  // Evaluation operations
  runAgent: (workflowId: string) => `api/evaluation/${encodeURIComponent(workflowId)}/run-agent`,
  generateCases: (workflowId: string) =>
    `api/evaluation/${encodeURIComponent(workflowId)}/generate-cases`,
  runEvaluation: (workflowId: string) =>
    `api/evaluation/${encodeURIComponent(workflowId)}/run-evaluation`,
  saveCriteria: (workflowId: string) => `api/evaluation/${encodeURIComponent(workflowId)}/criteria`,

  // Delete operations
  deleteAgentTrace: (workflowId: string) =>
    `api/evaluation/${encodeURIComponent(workflowId)}/trace`,
  deleteEvaluationCriteria: (workflowId: string) =>
    `api/evaluation/${encodeURIComponent(workflowId)}/criteria`,
  deleteEvaluationResults: (workflowId: string) =>
    `api/evaluation/${encodeURIComponent(workflowId)}/results`,
}
