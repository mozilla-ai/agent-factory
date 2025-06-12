import { apiClient } from './api'

export const evaluationService = {
  async runAgent(workflowPath: string): Promise<Response> {
    return apiClient.post(
      `/agent-factory/evaluate/run-agent/${workflowPath}`,
      {},
      {
        responseType: 'stream',
      },
    )
  },

  async generateCases(workflowPath: string): Promise<Response> {
    return apiClient.post(
      `/agent-factory/evaluate/generate-cases/${workflowPath}`,
      {},
      {
        responseType: 'stream',
      },
    )
  },

  async runEvaluation(workflowPath: string): Promise<Response> {
    return apiClient.post(
      `/agent-factory/evaluate/run-evaluation/${workflowPath}`,
      {},
      {
        responseType: 'stream',
      },
    )
  },
}
