import { API_CONFIG } from '@/config/api.config'
import { handleApiError } from './error.helpers'

/**
 * Generic helper for streaming POST endpoints
 */
export async function fetchStream(endpoint: string, context: string): Promise<ReadableStream> {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/${endpoint}`, {
      method: 'POST',
    })

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}: ${response.statusText}`)
    }

    return response.body as ReadableStream
  } catch (error) {
    handleApiError(error, context)
  }
}
