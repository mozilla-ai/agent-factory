const API_BASE_URL = 'http://localhost:3000/agent-factory'

/**
 * API service for file-related operations
 */
export const fileApi = {
  /**
   * Check if a file exists at the specified path
   */
  async checkFileExists(filePath: string): Promise<boolean> {
    try {
      const encodedPath = encodeURIComponent(filePath)
      const response = await fetch(`${API_BASE_URL}/workflows/${encodedPath}`, {
        method: 'GET'
      })

      return response.ok
    } catch (error) {
      console.error(`Error checking if file exists: ${filePath}`, error)
      return false
    }
  },

  /**
   * Get file content from the specified path
   */
  async getFileContent(filePath: string): Promise<string> {
    try {
      const encodedPath = encodeURIComponent(filePath)
      const response = await fetch(`${API_BASE_URL}/workflows/${encodedPath}`)

      if (!response.ok) {
        throw new Error(`Failed to load file: ${response.status} ${response.statusText}`)
      }

      // Handle binary files
      const contentType = response.headers.get('content-type')
      if (contentType && !contentType.includes('text/') && !contentType.includes('application/json')) {
        const downloadUrl = `${API_BASE_URL}/workflows/${encodedPath}`
        return `[This is a binary file (${contentType}) and cannot be displayed inline]\n\nYou can download it at: ${downloadUrl}`
      }

      return await response.text()
    } catch (error) {
      console.error('Error loading file:', error)
      throw error
    }
  }
}
