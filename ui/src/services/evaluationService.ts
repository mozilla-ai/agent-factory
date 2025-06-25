import { apiClient } from './api'
import Yaml from 'yaml'
import { workflowService } from './workflowService'
import { ENDPOINTS } from '@/config/endpoints'
import { getErrorMessage } from '@/helpers/error.helpers'
import { fetchStream } from '@/helpers/stream.helpers'
import type { EvaluationCriteria, SaveCriteriaResponse } from '@/types/index'

export const evaluationService = {
  async runAgent(workflowId: string): Promise<ReadableStream> {
    return fetchStream(ENDPOINTS.runAgent(workflowId), 'run agent')
  },

  async generateEvaluationCases(workflowId: string): Promise<ReadableStream> {
    return fetchStream(ENDPOINTS.generateCases(workflowId), 'generate evaluation cases')
  },

  async runEvaluation(workflowId: string): Promise<ReadableStream> {
    return fetchStream(ENDPOINTS.runEvaluation(workflowId), 'run evaluation')
  },

  async getEvaluationCriteria(workflowId: string): Promise<EvaluationCriteria> {
    const content = await workflowService.getFileContent(workflowId, 'evaluation_case.yaml')
    return Yaml.parse(content)
  },

  async saveEvaluationCriteria(
    workflowId: string,
    criteriaData: EvaluationCriteria,
  ): Promise<SaveCriteriaResponse> {
    try {
      const response = await apiClient.post(ENDPOINTS.saveCriteria(workflowId), criteriaData)
      return response.data
    } catch (error) {
      const message = getErrorMessage(error)
      console.error('API Error in saving evaluation criteria:', error)
      throw new Error(message)
    }
  },

  /**
   * Get evaluation results for a workflow
   */
  async getEvaluationResults(workflowId: string): Promise<string> {
    return await workflowService.getFileContent(workflowId, 'evaluation_results.json')
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
