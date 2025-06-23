// Base API configuration and helpers
import axios from 'axios'
import { API_CONFIG } from '@/config/api.config'

export const apiClient = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Global error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Global error handling (logging, notifications)
    return Promise.reject(error)
  },
)

// getWorkflowUrl removed - file endpoints handled directly by workflowService
