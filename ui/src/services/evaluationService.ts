import { apiClient } from './api'
import { workflowService } from './workflowService'
import { ENDPOINTS } from '@/config/endpoints'
import { API_CONFIG } from '@/config/api.config'
import { getErrorMessage } from '@/helpers/error.helpers'
import { fetchStream } from '@/helpers/stream.helpers'
import type { EvaluationCriteria, ExecutionCosts, SaveCriteriaResponse } from '@/types/index'

// Simple evaluation case format with just criteria strings
interface SimpleCriteriaFormat {
  criteria: string[]
  evaluation_case_generation_costs: ExecutionCosts
}

// Transform function to convert simple format to full UI format
function transformToUIFormat(simpleFormat: SimpleCriteriaFormat): EvaluationCriteria {
  return {
    llm_judge: 'gpt-4.1', // Default value since not in current format
    checkpoints: simpleFormat.criteria.map((criterion) => ({
      criteria: criterion,
      points: 1, // Default fallback value
    })),
    evaluation_case_generation_costs: simpleFormat.evaluation_case_generation_costs,
  }
}

export const evaluationService = {
  async runAgent(workflowId: string): Promise<ReadableStream> {
    return fetchStream(`${API_CONFIG.baseURL}/${ENDPOINTS.runAgent(workflowId)}`, 'run agent', {
      method: 'POST',
    })
  },

  async generateEvaluationCases(workflowId: string): Promise<ReadableStream> {
    return fetchStream(
      `${API_CONFIG.baseURL}/${ENDPOINTS.generateCases(workflowId)}`,
      'generate evaluation cases',
      { method: 'POST' },
    )
  },

  async runEvaluation(workflowId: string): Promise<ReadableStream> {
    return fetchStream(
      `${API_CONFIG.baseURL}/${ENDPOINTS.runEvaluation(workflowId)}`,
      'run evaluation',
      { method: 'POST' },
    )
  },

  async getEvaluationCriteria(workflowId: string): Promise<EvaluationCriteria> {
    try {
      const content = await workflowService.getFileContent(workflowId, 'evaluation_case.json')

      // Check if content is already parsed (object) or needs parsing (string)
      const simpleFormat: SimpleCriteriaFormat =
        typeof content === 'string' ? JSON.parse(content) : content

      // Transform simple format to UI format for backward compatibility with UI components
      return transformToUIFormat(simpleFormat)
    } catch (error) {
      console.error('Error loading evaluation criteria:', error)
      throw error
    }
  },

  async saveCriteria(
    workflowId: string,
    criteria: EvaluationCriteria,
  ): Promise<SaveCriteriaResponse> {
    try {
      const response = await apiClient.post(ENDPOINTS.saveCriteria(workflowId), criteria)
      return response.data
    } catch (error) {
      throw new Error('Failed to save evaluation criteria: ' + getErrorMessage(error))
    }
  },

  /**
   * Get evaluation results for a workflow
   */
  async getEvaluationResults(workflowId: string): Promise<string> {
    const content = await workflowService.getFileContent(workflowId, 'evaluation_results.json')
    return typeof content === 'string' ? content : JSON.stringify(content)
  },

  /**
   * Delete evaluation criteria for a workflow
   */
  async deleteEvaluationCriteria(
    workflowId: string,
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(ENDPOINTS.deleteEvaluationCriteria(workflowId))
    return response.data
  },

  /**
   * Delete evaluation results for a workflow
   */
  async deleteEvaluationResults(
    workflowId: string,
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(ENDPOINTS.deleteEvaluationResults(workflowId))
    return response.data
  },

  /**
   * Delete agent evaluation trace for a workflow
   */
  async deleteAgentEvalTrace(workflowId: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(ENDPOINTS.deleteAgentTrace(workflowId))
    return response.data
  },
}
