import { apiClient } from './api'
import { workflowService } from './workflowService'
import { ENDPOINTS } from '@/config/endpoints'
import { API_CONFIG } from '@/config/api.config'
import { getErrorMessage } from '@/helpers/error.helpers'
import { fetchStream } from '@/helpers/stream.helpers'
import type { EvaluationCriteria, SaveCriteriaResponse } from '@/types/index'

// Current simple JSON structure from Python
interface SimpleEvaluationCase {
  criteria: string[]
}

// Future enhanced JSON structure that might include points
interface EnhancedEvaluationCase {
  criteria: Array<{
    criteria: string
    points?: number
  }>
  llm_judge?: string
}

// Union type to handle both current and future formats
type NewEvaluationCase = SimpleEvaluationCase | EnhancedEvaluationCase

// Type guard to check if it's the enhanced format
function isEnhancedFormat(data: NewEvaluationCase): data is EnhancedEvaluationCase {
  return Array.isArray(data.criteria) &&
         data.criteria.length > 0 &&
         typeof data.criteria[0] === 'object' &&
         'criteria' in data.criteria[0]
}

// Transform function to convert new JSON format to old structure
function transformToOldFormat(newFormat: NewEvaluationCase): EvaluationCriteria {
  if (isEnhancedFormat(newFormat)) {
    // Handle future enhanced format with potential points
    return {
      llm_judge: newFormat.llm_judge || 'gpt-4.1',
      checkpoints: newFormat.criteria.map((item) => ({
        criteria: item.criteria,
        points: item.points || 0, // Use provided points or fallback to 0
      }))
    }
  } else {
    // Handle current simple format
    return {
      llm_judge: 'gpt-4.1', // Default value since not in current format
      checkpoints: newFormat.criteria.map((criterion) => ({
        criteria: criterion,
        points: 0, // Default fallback value to indicate not set
      }))
    }
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
      const newFormat: NewEvaluationCase = typeof content === 'string' ? JSON.parse(content) : content

      // Transform new format to old format for backward compatibility with UI components
      return transformToOldFormat(newFormat)
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
