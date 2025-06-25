import { apiClient } from './api'
import type { WorkflowFile, EvaluationStatus } from '@/types'

export const workflowService = {
  async getWorkflows(): Promise<WorkflowFile[]> {
    const response = await apiClient.get('/agent-factory/workflows')
    return response.data
  },

  async getFileContent(workflowPath: string, filePath: string): Promise<string> {
    const response = await apiClient.get(`/agent-factory/workflows/${workflowPath}/${filePath}`, {
      transformResponse: [(data) => data], // Prevent JSON parsing
    })
    return response.data
  },

  async checkFileExists(workflowPath: string, filePath: string): Promise<boolean> {
    try {
      await apiClient.head(`/agent-factory/workflows/${workflowPath}/${filePath}`)
      return true
    } catch {
      return false
    }
  },

  async getEvaluationStatus(workflowPath: string): Promise<EvaluationStatus> {
    // Implement file checks for evaluation status
    const [hasAgentTrace, hasEvalCases, hasEvalResults] = await Promise.all([
      this.checkFileExists(workflowPath, 'agent_eval_trace.json'),
      this.checkFileExists(workflowPath, 'evaluation_case.json'),
      this.checkFileExists(workflowPath, 'evaluation_results.json'),
    ])

    return { hasAgentTrace, hasEvalCases, hasEvalResults }
  },

  async getEvaluationResults(workflowPath: string) {
    const response = await apiClient.get(
      `/agent-factory/workflows/${workflowPath}/evaluation_results.json`,
    )
    return response.data
  },

  async getAgentTrace(workflowPath: string) {
    const response = await apiClient.get(
      `/agent-factory/workflows/${workflowPath}/agent_eval_trace.json`,
    )
    return response.data
  },

  async getEvaluationCriteria(workflowPath: string) {
    const response = await apiClient.get(
      `/agent-factory/workflows/${workflowPath}/evaluation_case.json`,
    )
    return response.data
  },
}
