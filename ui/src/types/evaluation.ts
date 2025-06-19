export interface EvaluationCheckpoint {
  criteria: string
  points: number
}

export interface EvaluationCriteria {
  llm_judge: string
  checkpoints: EvaluationCheckpoint[]
}

export interface EvaluationResult {
  criteria: string
  result: 'pass' | 'fail'
  feedback: string
}

export interface SaveCriteriaResponse {
  success: boolean
  message: string
  path: string
}
