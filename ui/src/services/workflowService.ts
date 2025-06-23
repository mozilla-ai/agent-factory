import { apiClient } from './api'
import { ENDPOINTS } from '@/config/endpoints'
import type { WorkflowFile, EvaluationStatus, AgentTrace } from '@/types'

export const workflowService = {
  async getWorkflows(): Promise<WorkflowFile[]> {
    const response = await apiClient.get(ENDPOINTS.workflows)
    return response.data
  },
  async generateAgent(prompt: string): Promise<ReadableStream> {
    const response = await fetch(
      `${apiClient.defaults.baseURL}/${ENDPOINTS.generateAgent(prompt)}`,
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
    const response = await apiClient.get(ENDPOINTS.workflowFile(workflowId, filePath))
    return response.data
  },

  async checkFileExists(workflowId: string, filePath: string): Promise<boolean> {
    try {
      await apiClient.head(ENDPOINTS.workflowFile(workflowId, filePath))
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

  async getEvaluationResults(workflowId: string): Promise<string> {
    return this.getFileContent(workflowId, 'evaluation_results.json')
  },

  async getAgentTrace(workflowId: string): Promise<AgentTrace> {
    const content = await this.getFileContent(workflowId, 'agent_eval_trace.json')
    return content as unknown as AgentTrace
  },

  async getEvaluationCriteria(workflowId: string): Promise<string> {
    return this.getFileContent(workflowId, 'evaluation_case.yaml')
  },
}
