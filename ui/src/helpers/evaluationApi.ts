const API_BASE_URL = 'http://localhost:3000/agent-factory/evaluate'

/**
 * API service for evaluation-related operations
 */
export const evaluationApi = {
  /**
   * Run the agent for a specific workflow
   */
  async runAgent(workflowPath: string): Promise<Response> {
    return fetch(`${API_BASE_URL}/run-agent/${workflowPath}`, {
      method: 'POST'
    })
  },

  /**
   * Generate evaluation cases for a workflow
   */
  async generateCases(workflowPath: string): Promise<Response> {
    return fetch(`${API_BASE_URL}/generate-cases/${workflowPath}`, {
      method: 'POST'
    })
  },

  /**
   * Run evaluation for a workflow
   */
  async runEvaluation(workflowPath: string): Promise<Response> {
    return fetch(`${API_BASE_URL}/run-evaluation/${workflowPath}`, {
      method: 'POST'
    })
  },

  /**
   * Get the evaluation status for a workflow
   */
  async getEvaluationStatus(workflowPath: string): Promise<{
    hasAgentTrace: boolean;
    hasEvalCases: boolean;
    hasEvalResults: boolean;
  }> {
    try {
      const results = await Promise.all([
        fetch(`${API_BASE_URL}/status/${workflowPath}/agent_eval_trace.json`, { method: 'GET' }),
        fetch(`${API_BASE_URL}/status/${workflowPath}/evaluation_case.yaml`, { method: 'GET' }),
        fetch(`${API_BASE_URL}/status/${workflowPath}/evaluation_results.json`, { method: 'GET' })
      ])

      return {
        hasAgentTrace: results[0].ok,
        hasEvalCases: results[1].ok,
        hasEvalResults: results[2].ok
      }
    } catch (error) {
      console.error('Error checking evaluation status:', error)
      return {
        hasAgentTrace: false,
        hasEvalCases: false,
        hasEvalResults: false
      }
    }
  }
}
