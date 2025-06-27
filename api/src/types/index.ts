import { z } from 'zod'

// File system types
export interface FileEntry {
  name: string
  isDirectory: boolean
  path?: string
  files?: FileEntry[]
}

// Callback types
export type OutputCallback = (source: 'stdout' | 'stderr', text: string) => void

// API Response types
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: string
  message?: string
  details?: unknown
}

export interface ApiError {
  status: number
  message: string
  code?: string
  details?: unknown
}

// Evaluation types
export interface EvaluationCheckpoint {
  criteria: string
  points: number
}

export interface EvaluationCriteria {
  llm_judge: string
  checkpoints: EvaluationCheckpoint[]
}

export interface EvaluationResult {
  passed: boolean
  score: number
  totalPoints: number
  checkpoints: Array<{
    criteria: string
    points: number
    passed: boolean
    feedback?: string
  }>
}

// Workflow types
export interface WorkflowInfo {
  name: string
  path: string
  hasAgent: boolean
  hasEvaluationCriteria: boolean
  hasEvaluationResults: boolean
  hasAgentTrace: boolean
  lastModified?: Date
  files?: FileEntry[]
  isDirectory?: boolean
}

// Request validation schemas
export const GenerateAgentSchema = z.object({
  prompt: z.string().min(1).optional(),
})

export const SendInputSchema = z.object({
  input: z.string().min(1),
})

export const SaveEvaluationCriteriaSchema = z.object({
  llm_judge: z.string().min(1),
  checkpoints: z
    .array(
      z.object({
        criteria: z.string().min(1),
        points: z.number().positive(),
      }),
    )
    .min(1),
})

export const WorkflowPathSchema = z.object({
  workflowPath: z.string().min(1),
})

// Process management types
export interface ProcessInfo {
  pid?: number
  isRunning: boolean
  startTime?: Date
}

// Configuration types
export interface ApiConfig {
  port: number
  workflowsDir: string
  pythonExecutable: string
  uvExecutable: string
  agentFactoryExecutable: string
  environment: 'development' | 'production' | 'test'
  rootDir: string
}

// Export type helpers
export type RequestHandler<T = unknown> = (
  req: {
    body: T
    params: Record<string, string>
    query: Record<string, string>
  },
  res: {
    status: (code: number) => {
      json: (data: unknown) => void
      send: (data: string) => void
    }
    json: (data: unknown) => void
    send: (data: string) => void
    write: (data: string) => void
    end: (data?: string) => void
    setHeader: (name: string, value: string) => void
  },
) => Promise<void> | void
