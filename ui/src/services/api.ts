import type { Workflow } from '../types/workflow'

const API_BASE_URL = 'http://localhost:3000/agent-factory'

export const api = {
  /**
   * Fetch all workflows
   */
  async getWorkflows(): Promise<Workflow[]> {
    const response = await fetch(`${API_BASE_URL}/workflows`)

    if (!response.ok) {
      throw new Error(`Failed to fetch workflows: ${response.status} ${response.statusText}`)
    }

    return response.json()
  },

  /**
   * Fetch a specific workflow by ID
   */
  async getWorkflowById(id: string): Promise<Workflow> {
    const response = await fetch(`${API_BASE_URL}/workflows/${id}`)

    if (!response.ok) {
      throw new Error(`Failed to fetch workflow: ${response.status} ${response.statusText}`)
    }

    return response.json()
  },

  /**
   * Fetch file content
   */
  async getFileContent(filePath: string): Promise<string> {
    const encodedPath = encodeURIComponent(filePath)
    const response = await fetch(`${API_BASE_URL}/workflows/${encodedPath}`)

    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.status} ${response.statusText}`)
    }

    return response.text()
  },

  /**
   * Check if a file exists
   */
  async checkFileExists(filePath: string): Promise<boolean> {
    try {
      const encodedPath = encodeURIComponent(filePath)
      const response = await fetch(`${API_BASE_URL}/workflows/${encodedPath}`, {
        method: 'GET'
      })
      return response.ok
    } catch {
      return false
    }
  }
}
