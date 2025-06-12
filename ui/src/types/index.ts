export interface WorkflowFile {
  name: string
  isDirectory: boolean
  files?: WorkflowFile[]
  path?: string
}

export interface Workflow {
  name: string
  isDirectory: boolean
  files?: WorkflowFile[]
  path?: string
}

export interface EvaluationStatus {
  hasAgentTrace: boolean
  hasEvalCases: boolean
  hasEvalResults: boolean
}

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

export interface EvaluationCheckpoint {
  criteria: string
  result: 'pass' | 'fail'
  points: number
  feedback?: string
  // Add other properties that exist in your checkpoints
}
