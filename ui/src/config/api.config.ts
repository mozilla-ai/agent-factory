/**
 * Centralized API configuration
 */

export const API_CONFIG = {
  baseURL: import.meta.env.VITE_APP_API_BASE_URL || 'http://localhost:3000',
  timeout: 30000,
} as const

/**
 * Get the base URL for API requests
 */
export function getApiBaseUrl(): string {
  return API_CONFIG.baseURL
}

// Removed getWorkflowUrl - file access endpoints should be handled directly by services

// Endpoints moved to /config/endpoints.ts
