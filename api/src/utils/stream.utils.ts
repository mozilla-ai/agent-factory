import { Response } from 'express'

// Common streaming handler setup for evaluation endpoints
export function setupStreamingResponse(res: Response) {
  res.setHeader('Content-Type', 'text/plain; charset=utf-8')
  return (source: 'stdout' | 'stderr', text: string) => {
    if (source === 'stdout') {
      console.log(`[evaluation stdout]: ${text}`)
      res.write(`[stdout]: ${text}`)
    } else if (source === 'stderr') {
      console.log(`[evaluation stderr]: ${text}`)
      res.write(`[stderr]: ${text}`)
    }
  }
}
