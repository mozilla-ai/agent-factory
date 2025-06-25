// Define types for the evaluation data structures
interface CheckpointResult {
  passed: boolean
  reason: string
  criteria: string
  points: number
}

interface NewFormatData {
  obtained_score: number
  max_score: number
  checkpoint_results: CheckpointResult[]
}

interface TransformedCheckpoint {
  result: 'pass' | 'fail'
  feedback: string
  criteria: string
  points: number
}

export interface OldFormatData {
  checkpoints: TransformedCheckpoint[]
  totalScore: number
  maxPossibleScore: number
  score: number
  maxScore: number
}

// Transform results to align with criteria
export const transformResults = (data: NewFormatData | OldFormatData): OldFormatData => {
  // If it's already in the old format, return it as is
  if ('checkpoints' in data && data.checkpoints) {
    return data
  }

  const newData = data as NewFormatData

  // Transform from new format to old format
  return {
    // Add metadata from new format
    totalScore: newData.obtained_score,
    maxPossibleScore: newData.max_score,
    score: newData.obtained_score,
    maxScore: newData.max_score,

    // Transform checkpoint results to match the expected format
    checkpoints: newData.checkpoint_results.map((checkpoint: CheckpointResult) => ({
      result: checkpoint.passed ? 'pass' : 'fail',
      feedback: checkpoint.reason,
      criteria: checkpoint.criteria,
      points: checkpoint.points,
    })),
  }
}
