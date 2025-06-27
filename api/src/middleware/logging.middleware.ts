import { Request, Response, NextFunction } from 'express'

export function requestLogger(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const start = Date.now()
  const timestamp = new Date().toISOString()

  // Log the incoming request
  console.log(`[${timestamp}] ${req.method} ${req.path}`)

  // Log query params if present
  if (Object.keys(req.query).length > 0) {
    console.log(`  Query:`, req.query)
  }

  // Log request body if present (but truncate large bodies)
  if (req.body && Object.keys(req.body).length > 0) {
    const bodyStr = JSON.stringify(req.body)
    const truncatedBody =
      bodyStr.length > 500 ? bodyStr.substring(0, 500) + '...' : bodyStr
    console.log(`  Body:`, truncatedBody)
  }

  // Capture the original res.json and res.send to log responses
  const originalJson = res.json
  const originalSend = res.send

  res.json = function (body: unknown) {
    const duration = Date.now() - start
    console.log(
      `[${timestamp}] ${req.method} ${req.path} - ${res.statusCode} (${duration}ms)`,
    )

    // Log response body for errors or if it's small
    if (res.statusCode >= 400 || (body && JSON.stringify(body).length < 200)) {
      console.log(`  Response:`, body)
    }

    return originalJson.call(this, body)
  }

  res.send = function (body: unknown) {
    const duration = Date.now() - start
    console.log(
      `[${timestamp}] ${req.method} ${req.path} - ${res.statusCode} (${duration}ms)`,
    )

    // Log response body for errors or if it's small
    if (
      res.statusCode >= 400 &&
      body &&
      typeof body === 'string' &&
      body.length < 200
    ) {
      console.log(`  Response:`, body)
    }

    return originalSend.call(this, body)
  }

  next()
}

// Simple middleware to log unhandled errors
export function errorLogger(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  console.error(`[ERROR] ${req.method} ${req.path}:`, {
    message: err.message,
    stack: err.stack,
    body: req.body,
    params: req.params,
    query: req.query,
  })

  next(err)
}
