// Base API configuration and helpers
import axios from 'axios'

// Read from environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Global error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Global error handling (logging, notifications)
    // console.error('API Error:', error)
    return Promise.reject(error)
  },
)

export function getWorkflowUrl(workflowPath: string, filePath?: string): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'
  const endpoint = `/agent-factory/workflows/${workflowPath}`
  return filePath ? `${baseUrl}${endpoint}/${filePath}` : `${baseUrl}${endpoint}`
}
