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

export async function getEvaluationCriteria(workflowPath: string): Promise<EvaluationCriteria> {
  const response = await apiClient.get(
    `/agent-factory/workflows/${encodeURIComponent(workflowPath)}/evaluation_case.yaml`,
  )
  return Yaml.parse(response.data) // Ensure the response is parsed as YAML
}

export async function saveEvaluationCriteria(
  workflowPath: string,
  criteriaData: EvaluationCriteria,
): Promise<SaveCriteriaResponse> {
  const response = await apiClient.post(
    `/agent-factory/evaluate/save-criteria/${encodeURIComponent(workflowPath)}`,
    criteriaData,
  )
  return response.data
}

export async function getEvaluationResults(workflowPath: string) {
  const response = await apiClient.get(
    `/agent-factory/workflows/${encodeURIComponent(workflowPath)}/evaluation_results.json`,
  )
  return response.data
}

/**
 * Delete evaluation criteria for a workflow
 */
export async function deleteEvaluationCriteria(
  workflowPath: string,
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete(
    `/agent-factory/workflows/${workflowPath}/evaluation_criteria`,
  )
  return response.data
}

/**
 * Delete evaluation results for a workflow
 */
export async function deleteEvaluationResults(
  workflowPath: string,
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete(
    `/agent-factory/workflows/${workflowPath}/evaluation_results`,
  )
  return response.data
}

/**
 * Delete agent evaluation trace for a workflow
 */
export async function deleteAgentEvalTrace(
  workflowPath: string,
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete(
    `/agent-factory/workflows/${workflowPath}/agent_eval_trace`,
  )
  return response.data
}
