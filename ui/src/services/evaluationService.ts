import { apiClient } from './api'

export const evaluationService = {
  async runAgent(workflowPath: string): Promise<ReadableStream> {
    const response = await fetch(
      `${apiClient.defaults.baseURL}/agent-factory/evaluate/run-agent/${encodeURIComponent(workflowPath)}`,
      { method: 'POST' },
    )

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`)
    }

    // Return the native ReadableStream from fetch
    return response.body as ReadableStream
  },

  async generateEvaluationCases(workflowPath: string): Promise<ReadableStream> {
    const response = await fetch(
      `${apiClient.defaults.baseURL}/agent-factory/evaluate/generate-cases/${encodeURIComponent(workflowPath)}`,
      { method: 'POST' },
    )

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`)
    }

    return response.body as ReadableStream
  },

  async runEvaluation(workflowPath: string): Promise<ReadableStream> {
    const response = await fetch(
      `${apiClient.defaults.baseURL}/agent-factory/evaluate/run-evaluation/${encodeURIComponent(workflowPath)}`,
      { method: 'POST' },
    )

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`)
    }

    return response.body as ReadableStream
  },
}
