import { Request, Response, NextFunction } from 'express'
import { ZodError } from 'zod'
import type { ApiResponse } from '../types/index.js'
import { isProduction } from '../config/index.js'

export class AppError extends Error {
  public readonly status: number
  public readonly code?: string
  public readonly details?: unknown

  constructor(
    message: string,
    status: number = 500,
    code?: string,
    details?: unknown,
  ) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
    this.name = 'AppError'

    // Maintains proper stack trace for where our error was thrown
    Error.captureStackTrace(this, this.constructor)
  }
}

// Specific error types
export class ValidationError extends AppError {
  constructor(message: string, details?: unknown) {
    super(message, 400, 'VALIDATION_ERROR', details)
  }
}

export class NotFoundError extends AppError {
  constructor(message: string = 'Resource not found') {
    super(message, 404, 'NOT_FOUND')
  }
}

export class ProcessError extends AppError {
  constructor(message: string, details?: unknown) {
    super(message, 500, 'PROCESS_ERROR', details)
  }
}

export class FileOperationError extends AppError {
  constructor(message: string, details?: unknown) {
    super(message, 500, 'FILE_OPERATION_ERROR', details)
  }
}

// Error response formatter
function formatErrorResponse(error: AppError): ApiResponse {
  const response: ApiResponse = {
    success: false,
    error: error.message,
  }

  // Include additional details in development
  if (!isProduction()) {
    response.details = {
      code: error.code,
      stack: error.stack,
      details: error.details,
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
    const validationError = new ValidationError(
      'Invalid request data',
      err.errors.map((e) => ({
        path: e.path.join('.'),
        message: e.message,
        code: e.code,
      })),
    )

    res
      .status(validationError.status)
      .json(formatErrorResponse(validationError))
    return
  }

  // Handle our custom app errors
  if (err instanceof AppError) {
    res.status(err.status).json(formatErrorResponse(err))
    return
  }

  // Handle unexpected errors
  const unexpectedError = new AppError(
    isProduction() ? 'Internal server error' : err.message,
    500,
    'INTERNAL_ERROR',
    !isProduction()
      ? { originalError: err.message, stack: err.stack }
      : undefined,
  )

  res.status(500).json(formatErrorResponse(unexpectedError))
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
  const error = new NotFoundError(`Route ${req.method} ${req.path} not found`)
  res.status(error.status).json(formatErrorResponse(error))
}
