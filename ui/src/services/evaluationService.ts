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
  async runAgent(workflowId: string): Promise<ReadableStream> {
    const response = await fetch(
      `${apiClient.defaults.baseURL}/agent-factory/evaluate/run-agent/${encodeURIComponent(workflowId)}`,
      { method: 'POST' },
    )

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`)
    }

    return response.body as ReadableStream
  },

  async generateEvaluationCases(workflowId: string): Promise<ReadableStream> {
    const response = await fetch(
      `${apiClient.defaults.baseURL}/agent-factory/evaluate/generate-cases/${encodeURIComponent(workflowId)}`,
      { method: 'POST' },
    )

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`)
    }

    return response.body as ReadableStream
  },

  async runEvaluation(workflowId: string): Promise<ReadableStream> {
    const response = await fetch(
      `${apiClient.defaults.baseURL}/agent-factory/evaluate/run-evaluation/${encodeURIComponent(workflowId)}`,
      { method: 'POST' },
    )

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`)
    }

    return response.body as ReadableStream
  },
  async getEvaluationCriteria(workflowId: string): Promise<EvaluationCriteria> {
    const response = await apiClient.get(
      `/agent-factory/workflows/${encodeURIComponent(workflowId)}/evaluation_case.yaml`,
    )
    return Yaml.parse(response.data) // Ensure the response is parsed as YAML
  },
  async saveEvaluationCriteria(
    workflowId: string,
    criteriaData: EvaluationCriteria,
  ): Promise<SaveCriteriaResponse> {
    const response = await apiClient.post(
      `/agent-factory/evaluate/save-criteria/${encodeURIComponent(workflowId)}`,
      criteriaData,
    )
    return response.data
  },

  /**
   * Get evaluation results for a workflow
   */
  async getEvaluationResults(workflowId: string) {
    const response = await apiClient.get(
      `/agent-factory/workflows/${encodeURIComponent(workflowId)}/evaluation_results.json`,
    )
    return response.data
  },

  /**
   * Delete evaluation criteria for a workflow
   */
  async deleteEvaluationCriteria(
    workflowId: string,
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(
      `/agent-factory/workflows/${encodeURIComponent(workflowId)}/evaluation_criteria`,
    )
    return response.data
  },

  /**
   * Delete evaluation results for a workflow
   */
  async deleteEvaluationResults(
    workflowId: string,
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(
      `/agent-factory/workflows/${encodeURIComponent(workflowId)}/evaluation_results`,
    )
    return response.data
  },

  /**
   * Delete agent evaluation trace for a workflow
   */
  async deleteAgentEvalTrace(workflowId: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(
      `/agent-factory/workflows/${encodeURIComponent(workflowId)}/agent_eval_trace`,
    )
    return response.data
  },
}
