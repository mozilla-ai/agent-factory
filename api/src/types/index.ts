export interface FileEntry {
  name: string
  isDirectory: boolean
  files?: FileEntry[]
}

export interface EvaluationCheckpointResult {
  criteria: string
  points: number
  result: 'pass' | 'fail'
  feedback: string
}

export interface EvaluationResults {
  score: number
  maxScore: number
  checkpoints: EvaluationCheckpointResult[]
}

export type OutputCallback = (source: 'stdout' | 'stderr', text: string) => void
