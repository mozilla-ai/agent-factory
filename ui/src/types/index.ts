// File system types
export interface FileEntry {
  name: string
  isDirectory: boolean
  files?: FileEntry[]
  path?: string
}

export interface TransformedFileEntry extends FileEntry {
  path: string
}

export interface WorkflowFile {
  name: string
  isDirectory: boolean
  files?: WorkflowFile[]
  path?: string
}

// Current simple JSON structure from Python (raw format)
export interface SimpleEvaluationCase {
  criteria: string[]
}

// Future enhanced JSON structure that might include points and llm_judge
export interface EnhancedEvaluationCase {
  criteria: Array<{
    criteria: string
    points?: number
  }>
  llm_judge?: string
}

// Union type to handle both current and future formats
export type NewEvaluationCase = SimpleEvaluationCase | EnhancedEvaluationCase

// Evaluation types (UI internal format - always includes points for UI components)
export interface EvaluationCheckpoint {
  criteria: string
  points: number
  result?: 'pass' | 'fail'
  feedback?: string
}

export interface EvaluationCriteria {
  llm_judge?: string // Optional since new format doesn't always include it
  checkpoints: EvaluationCheckpoint[]
}

export interface EvaluationResult {
  criteria: string
  result: 'pass' | 'fail'
  feedback: string
}

export interface EvaluationResults {
  score: number
  maxScore: number
  criteria: string[]
}

export interface EvaluationStatus {
  hasAgentTrace: boolean
  hasEvalCases: boolean
  hasEvalResults: boolean
}

export interface SaveCriteriaResponse {
  success: boolean
  message: string
  path: string
}

// Agent trace types
export interface TraceMessage {
  role: string
  content: string
}

export interface TraceSpan {
  name: string
  kind: string
  parent: Record<string, unknown>
  start_time: number
  end_time: number
  status: {
    status_code: string
    description: string | null
  }
  context: Record<string, unknown>
  attributes: {
    'gen_ai.input.messages'?: string
    'gen_ai.output'?: string
    'gen_ai.tool.args'?: string
    'gen_ai.usage.input_tokens'?: number
    'gen_ai.usage.output_tokens'?: number
    'gen_ai.usage.input_cost'?: number
    'gen_ai.usage.output_cost'?: number
    [key: string]: unknown
  }
  links: unknown[]
  events: unknown[]
  resource: {
    attributes: Record<string, string>
    schema_url: string
  }
}

export interface AgentTrace {
  spans: TraceSpan[]
  final_output: string
}
