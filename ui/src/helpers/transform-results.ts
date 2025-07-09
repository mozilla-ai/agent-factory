// Simple evaluation result with pass/fail and reasoning
interface SimpleEvaluationResult {
  passed: boolean
  reasoning: string
}

// Simple evaluation results format from evaluation scripts
interface SimpleResultsFormat {
  obtained_score: number
  max_score: number
  results: SimpleEvaluationResult[]
  total_cost: number
}

// Import the existing EvaluationResults interface
import type { EvaluationResults } from '@/composables/useEvaluationScores'

// Type for evaluation criteria to merge with results
interface EvaluationCriteria {
  checkpoints: Array<{
    criteria: string
    points: number
  }>
}

// Transform results to align with criteria
export const transformResults = (
  data: SimpleResultsFormat,
  criteria?: EvaluationCriteria,
): EvaluationResults => {
  // Handle case where data might be incomplete or undefined
  if (!data || typeof data !== 'object') {
    return {
      checkpoints: [],
      totalScore: 0,
      maxPossibleScore: 0,
      score: 0,
      maxScore: 0,
      total_cost: 0,
    }
  }

  // Check if it's the simple format with 'results' array

  const simpleData = data as SimpleResultsFormat
  return {
    // Add metadata from simple format
    totalScore: simpleData.obtained_score || 0,
    maxPossibleScore: simpleData.max_score || 0,
    score: simpleData.obtained_score || 0,
    maxScore: simpleData.max_score || 0,

    // Transform results to match the expected format, combining with criteria if available
    checkpoints: simpleData.results.map((result: SimpleEvaluationResult, index: number) => {
      const criteriaItem = criteria?.checkpoints?.[index]
      return {
        result: result.passed ? 'pass' : 'fail',
        feedback: result.reasoning || '',
        criteria: criteriaItem?.criteria || `Evaluation Criterion ${index + 1}`,
        points: criteriaItem?.points || 1,
      }
    }),
    total_cost: simpleData.total_cost || 0,
  }
}
