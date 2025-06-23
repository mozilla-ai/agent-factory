import axios from 'axios'

/**
 * Utility functions for consistent error handling across the application
 */

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }

  // Handle AxiosError specifically
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data as Record<string, unknown>
    if (responseData?.message && typeof responseData.message === 'string') {
      return responseData.message
    }
    if (responseData?.detail && typeof responseData.detail === 'string') {
      return responseData.detail
    }
    if (error.response?.statusText) {
      return `${error.response.status}: ${error.response.statusText}`
    }
    return error.message
  }

  return String(error)
}

export function createErrorHandler(context: string) {
  return (error: unknown) => {
    const message = getErrorMessage(error)
    console.error(`Error in ${context}:`, error)
    return message
  }
}

export function handleApiError(error: unknown, context?: string): never {
  const message = getErrorMessage(error)
  const contextMsg = context ? ` in ${context}` : ''
  console.error(`API Error${contextMsg}:`, error)
  throw new Error(message)
}

/**
 * Enhanced error handler for HTTP responses with status-specific messages
 */
export function handleHttpError(error: unknown, context?: string): never {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status

    if (status === 403) {
      throw new Error('You do not have permission to perform this action')
    } else if (status === 404) {
      throw new Error('Resource not found - please check the path and try again')
    } else if (status === 500) {
      throw new Error('Server error - please try again later')
    } else if (status === 422) {
      throw new Error('Invalid data provided - please check your input')
    } else if (status === 401) {
      throw new Error('Authentication required - please log in')
    }
  }

  const contextMsg = context ? ` ${context}` : ''
  throw new Error(`Request failed${contextMsg}: ${getErrorMessage(error)}`)
}
