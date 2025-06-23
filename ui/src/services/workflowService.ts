import { apiClient } from './api'
import type { WorkflowFile, EvaluationStatus } from '@/types'

export const workflowService = {
  async getWorkflows(): Promise<WorkflowFile[]> {
    const response = await apiClient.get('/agent-factory/workflows')
    return response.data
  },
  async generateAgent(prompt: string): Promise<ReadableStream> {
    const response = await fetch(
      `${apiClient.defaults.baseURL}/agent-factory/generate-agent?prompt=${encodeURIComponent(prompt)}`,
      {
        method: 'GET',
      },
    )
    if (!response.ok) {
      throw new Error(`Failed to generate agent: ${response.status} ${response.statusText}`)
    }
    return response.body as ReadableStream
  },
  async getFileContent(workflowId: string, filePath: string): Promise<string> {
    const response = await apiClient.get(
      `/agent-factory/workflows/${encodeURIComponent(workflowId)}/${filePath}`,
    )
    return response.data
  },

  async checkFileExists(workflowId: string, filePath: string): Promise<boolean> {
    try {
      await apiClient.head(`/agent-factory/workflows/${encodeURIComponent(workflowId)}/${filePath}`)
      return true
    } catch {
      return false
    }
  },

  async getEvaluationStatus(workflowId: string): Promise<EvaluationStatus> {
    // Implement file checks for evaluation status
    const [hasAgentTrace, hasEvalCases, hasEvalResults] = await Promise.all([
      this.checkFileExists(workflowId, 'agent_eval_trace.json'),
      this.checkFileExists(workflowId, 'evaluation_case.yaml'),
      this.checkFileExists(workflowId, 'evaluation_results.json'),
    ])

    return { hasAgentTrace, hasEvalCases, hasEvalResults }
  },

  async getEvaluationResults(workflowId: string) {
    const response = await apiClient.get(
      `/agent-factory/workflows/${encodeURIComponent(workflowId)}/evaluation_results.json`,
    )
    return response.data
  },

  async getAgentTrace(workflowId: string) {
    const response = await apiClient.get(
      `/agent-factory/workflows/${encodeURIComponent(workflowId)}/agent_eval_trace.json`,
    )
    return response.data
  },

  async getEvaluationCriteria(workflowId: string) {
    const response = await apiClient.get(
      `/agent-factory/workflows/${encodeURIComponent(workflowId)}/evaluation_case.yaml`,
    )
    return response.data
  },
}
