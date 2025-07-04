import { apiClient } from './api'
import { ENDPOINTS } from '@/config/endpoints'
import { API_CONFIG } from '@/config/api.config'
import type { WorkflowFile, EvaluationStatus, AgentTrace } from '@/types'

export const workflowService = {
  async getWorkflows(): Promise<WorkflowFile[]> {
    const response = await apiClient.get(ENDPOINTS.workflows)
    return response.data
  },
  async generateAgent(prompt: string): Promise<ReadableStream> {
    const response = await fetch(`${API_CONFIG.baseURL}/${ENDPOINTS.generateAgent}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
    })
    if (!response.ok) {
      throw new Error(`Failed to generate agent: ${response.status} ${response.statusText}`)
    }
    return response.body as ReadableStream
  },
  async getFileContent(workflowId: string, filePath: string): Promise<string | object> {
    const response = await apiClient.get(ENDPOINTS.workflowFile(workflowId, filePath))
    // For JSON files, Axios automatically parses them, so we might get an object
    // For other files, we get a string
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
      this.checkFileExists(workflowId, 'evaluation_case.json'),
      this.checkFileExists(workflowId, 'evaluation_results.json'),
    ])

    return { hasAgentTrace, hasEvalCases, hasEvalResults }
  },

  async getEvaluationResults(workflowId: string): Promise<string> {
    const content = await this.getFileContent(workflowId, 'evaluation_results.json')
    return typeof content === 'string' ? content : JSON.stringify(content)
  },

  async getAgentTrace(workflowId: string): Promise<AgentTrace> {
    const content = await this.getFileContent(workflowId, 'agent_eval_trace.json')
    try {
      return typeof content === 'string' ? JSON.parse(content) : (content as AgentTrace)
    } catch (error) {
      throw new Error(`Failed to parse agent trace: ${error}`)
    }
  },

  async getAgentGenerationTrace(workflowId: string): Promise<AgentTrace> {
    const content = await this.getFileContent(workflowId, 'agent_factory_trace.json')
    return typeof content === 'string' ? JSON.parse(content) : (content as AgentTrace)
  },

  async getEvaluationCriteria(workflowId: string): Promise<string> {
    const content = await this.getFileContent(workflowId, 'evaluation_case.json')
    return typeof content === 'string' ? content : JSON.stringify(content)
  },
}
