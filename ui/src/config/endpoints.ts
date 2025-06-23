/**
 * All API endpoints in one place for easy migration
 */

export const ENDPOINTS = {
  // Workflows
  workflows: 'agent-factory/workflows',
  workflowFile: (workflowId: string, filePath: string) =>
    `agent-factory/workflows/${encodeURIComponent(workflowId)}/${filePath}`,

  // Agent generation
  generateAgent: (prompt: string) => `agent-factory?prompt=${encodeURIComponent(prompt)}`,

  // Evaluation
  runAgent: (workflowId: string) =>
    `agent-factory/evaluate/run-agent/${encodeURIComponent(workflowId)}`,
  generateCases: (workflowId: string) =>
    `agent-factory/evaluate/generate-cases/${encodeURIComponent(workflowId)}`,
  runEvaluation: (workflowId: string) =>
    `agent-factory/evaluate/run-evaluation/${encodeURIComponent(workflowId)}`,
  saveCriteria: (workflowId: string) =>
    `agent-factory/evaluate/save-criteria/${encodeURIComponent(workflowId)}`,

  // Delete operations
  deleteEvaluationCriteria: (workflowId: string) =>
    `agent-factory/workflows/${encodeURIComponent(workflowId)}/evaluation_criteria`,
  deleteEvaluationResults: (workflowId: string) =>
    `agent-factory/workflows/${encodeURIComponent(workflowId)}/evaluation_results`,
  deleteAgentTrace: (workflowId: string) =>
    `agent-factory/workflows/${encodeURIComponent(workflowId)}/agent_eval_trace`,
}
