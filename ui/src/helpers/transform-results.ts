// Define types for the evaluation data structures
interface CheckpointResult {
  passed: boolean
  reason: string
  criteria: string
  points: number
}

// Updated interface for the new evaluation results format
interface NewEvaluationResult {
  passed: boolean
  reasoning: string
}

interface NewFormatData {
  obtained_score: number
  max_score: number
  results: NewEvaluationResult[]
}

// Legacy format for backward compatibility
interface LegacyFormatData {
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

// Type for evaluation criteria to merge with results
interface EvaluationCriteria {
  checkpoints: Array<{
    criteria: string
    points: number
  }>
}

// Transform results to align with criteria
export const transformResults = (
  data: NewFormatData | LegacyFormatData | OldFormatData,
  criteria?: EvaluationCriteria
): OldFormatData => {
  // If it's already in the old format, return it as is
  if ('checkpoints' in data && data.checkpoints) {
    return data
  }

  // Handle case where data might be incomplete or undefined
  if (!data || typeof data !== 'object') {
    return {
      checkpoints: [],
      totalScore: 0,
      maxPossibleScore: 0,
      score: 0,
      maxScore: 0,
    }
  }

  // Check if it's the new format with 'results' array
  if ('results' in data && Array.isArray(data.results)) {
    const newData = data as NewFormatData
    return {
      // Add metadata from new format
      totalScore: newData.obtained_score || 0,
      maxPossibleScore: newData.max_score || 0,
      score: newData.obtained_score || 0,
      maxScore: newData.max_score || 0,

      // Transform results to match the expected format, combining with criteria if available
      checkpoints: newData.results.map((result: NewEvaluationResult, index: number) => {
        const criteriaItem = criteria?.checkpoints?.[index]
        return {
          result: result.passed ? 'pass' : 'fail',
          feedback: result.reasoning || '',
          criteria: criteriaItem?.criteria || `Evaluation Criterion ${index + 1}`,
          points: criteriaItem?.points || 0,
        }
      }),
    }
  }

  // Handle legacy format with 'checkpoint_results'
  if ('checkpoint_results' in data && Array.isArray(data.checkpoint_results)) {
    const legacyData = data as LegacyFormatData
    return {
      totalScore: legacyData.obtained_score || 0,
      maxPossibleScore: legacyData.max_score || 0,
      score: legacyData.obtained_score || 0,
      maxScore: legacyData.max_score || 0,

      checkpoints: legacyData.checkpoint_results.map((checkpoint: CheckpointResult) => ({
        result: checkpoint.passed ? 'pass' : 'fail',
        feedback: checkpoint.reason || '',
        criteria: checkpoint.criteria || '',
        points: checkpoint.points || 0,
      })),
    }
  }

  // Fallback for unknown format
  return {
    checkpoints: [],
    totalScore: 0,
    maxPossibleScore: 0,
    score: 0,
    maxScore: 0,
  }
}
