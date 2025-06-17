import { apiClient } from './api'
import type { EvaluationCriteria, SaveCriteriaResponse } from '../types/evaluation'

export const evaluationService = {
  async runAgent(workflowPath: string): Promise<ReadableStream> {
    const response = await fetch(
      `${apiClient.defaults.baseURL}/agent-factory/evaluate/run-agent/${encodeURIComponent(workflowPath)}`,
      { method: 'POST' },
    )

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`)
    }

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

export async function fetchEvaluationCriteria(workflowId: string): Promise<EvaluationCriteria> {
  const path = workflowId === 'latest' ? 'latest' : `archive/${workflowId}`

  const response = await apiClient.get(`/agent-factory/workflows/${path}/evaluation_case.yaml`)
  return response.data
}

export async function saveEvaluationCriteria(
  workflowId: string,
  criteriaData: EvaluationCriteria,
): Promise<SaveCriteriaResponse> {
  const path = workflowId === 'latest' ? 'latest' : `archive/${workflowId}`

  const response = await apiClient.post(
    `/agent-factory/evaluate/save-criteria/${path}`,
    criteriaData,
  )
  return response.data
}
