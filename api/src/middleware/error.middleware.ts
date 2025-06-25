import { Request, Response, NextFunction } from 'express'
import { ZodError } from 'zod'
import type { ApiResponse } from '../types/index.js'
import { config } from '../config/index.js'

// Error response formatter
function formatErrorResponse(error: Error): ApiResponse {
  const response: ApiResponse = {
    success: false,
    error: error.message,
  }

  // Include stack trace in development
  if (config.environment !== 'production') {
    response.details = {
      stack: error.stack,
    }
  }

  return response
}

// Global error handler middleware
export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  _next: NextFunction,
): void {
  console.error('Error occurred:', {
    message: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    body: req.body,
    params: req.params,
  })

  // Handle Zod validation errors
  if (err instanceof ZodError) {
    res.status(400).json({
      success: false,
      error: 'Invalid request data',
      details:
        config.environment !== 'production'
          ? {
              validation: err.errors.map((e) => ({
                path: e.path.join('.'),
                message: e.message,
                code: e.code,
              })),
              stack: err.stack,
            }
          : undefined,
    })
    return
  }

  // Handle all other errors as 500 internal server error
  res.status(500).json(formatErrorResponse(err))
}

// Async error wrapper
export function asyncHandler(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<void>,
) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next)
  }
}

// 404 handler
export function notFoundHandler(req: Request, res: Response): void {
  res.status(404).json({
    success: false,
    error: `Route ${req.method} ${req.path} not found`,
  })
}
