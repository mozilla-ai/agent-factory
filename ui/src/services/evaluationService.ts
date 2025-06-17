import { apiClient } from './api'
import Yaml from 'yaml'
export interface EvaluationCheckpoint {
  criteria: string
  points: number
}

export interface EvaluationCriteria {
  llm_judge: string
  checkpoints: EvaluationCheckpoint[]
}

export interface SaveCriteriaResponse {
  success: boolean
  message: string
  path: string
}

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

// Return to original implementation without manual YAML parsing
export async function getEvaluationCriteria(workflowPath: string): Promise<EvaluationCriteria> {
  const response = await apiClient.get(
    `/agent-factory/workflows/${encodeURIComponent(workflowPath)}/evaluation_case.yaml`,
  )
  return Yaml.parse(response.data) // Ensure the response is parsed as YAML
}

// Fix the save endpoint path - it might be different than what we assumed
export async function saveEvaluationCriteria(
  workflowPath: string,
  criteriaData: EvaluationCriteria,
): Promise<SaveCriteriaResponse> {
  // Fix the endpoint path to match what's expected by the server
  const response = await apiClient.post(
    `/agent-factory/evaluate/save-criteria/${encodeURIComponent(workflowPath)}`,
    criteriaData,
  )
  return response.data
}

// Use consistent endpoint pattern for results
export async function getEvaluationResults(workflowPath: string) {
  const response = await apiClient.get(
    `/agent-factory/workflows/${encodeURIComponent(workflowPath)}/evaluation_results.json`,
  )
  return response.data
}
