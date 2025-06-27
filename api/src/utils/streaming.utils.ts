import { Response } from 'express'

/**
 * Handle errors in streaming endpoints consistently
 */
export function handleStreamingError(
  res: Response,
  error: unknown,
  context: string,
): void {
  const errorMessage = error instanceof Error ? error.message : String(error)

  if (!res.headersSent) {
    // Stream hasn't started, send proper HTTP error
    res.status(500).send(`${context}: ${errorMessage}`)
  } else {
    // Stream is active, write error to stream and end
    res.write(`\n[FATAL ERROR] ${context}: ${errorMessage}\n`)
    res.end()
  }
}

/**
 * Setup streaming response headers
 */
export function setupStreamingResponse(res: Response): void {
  res.setHeader('Content-Type', 'text/plain')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')
}

/**
 * Complete streaming response with success message
 */
export function completeStreamingResponse(
  res: Response,
  successMessage: string,
): void {
  res.write(`\n${successMessage}\n`)
  res.end()
}
