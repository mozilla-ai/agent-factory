import { computed, type Ref } from 'vue'
import type { EvaluationCriteria } from '@/types/evaluation'

export interface EvaluationResults {
  checkpoints: Array<{
    result: 'pass' | 'fail'
    feedback?: string
    criteria: string
    points: number
  }>
  totalScore: number
  maxPossibleScore: number
  score: number
  maxScore: number
}

export function useEvaluationScores(
  criteria: Ref<EvaluationCriteria | undefined>,
  results: Ref<EvaluationResults | undefined>,
) {
  // Calculate total possible points from criteria
  const totalPossiblePoints = computed(() => {
    if (!criteria.value?.checkpoints) return 0
    return criteria.value.checkpoints.reduce((sum, checkpoint) => sum + checkpoint.points, 0)
  })

  // Calculate total score from results
  const totalScore = computed(() => {
    if (!results.value?.checkpoints) return 0
    return results.value.checkpoints.reduce((sum, checkpoint) => {
      return sum + (checkpoint.result === 'pass' ? checkpoint.points : 0)
    }, 0)
  })

  // Calculate passed checkpoints count
  const passedCheckpoints = computed(() => {
    if (!results.value?.checkpoints) return 0
    return results.value.checkpoints.filter((checkpoint) => checkpoint.result === 'pass').length
  })

  // Calculate failed checkpoints count
  const failedCheckpoints = computed(() => {
    if (!results.value?.checkpoints) return 0
    return results.value.checkpoints.filter((checkpoint) => checkpoint.result === 'fail').length
  })

  // Calculate percentage score
  const scorePercentage = computed(() => {
    if (totalPossiblePoints.value === 0) return 0
    return Math.round((totalScore.value / totalPossiblePoints.value) * 100)
  })

  // Calculate pass rate percentage
  const passRate = computed(() => {
    const totalCheckpoints = results.value?.checkpoints?.length || 0
    if (totalCheckpoints === 0) return 0
    return Math.round((passedCheckpoints.value / totalCheckpoints) * 100)
  })

  // Check if we have valid score data
  const hasValidScoreData = computed(() => {
    return !!(results.value?.checkpoints?.length && totalPossiblePoints.value > 0)
  })

  // Get color threshold for progress bars based on score
  const scoreColorThreshold = computed(() => {
    if (scorePercentage.value >= 80) return 'success'
    if (scorePercentage.value >= 50) return 'warning'
    return 'error'
  })

  return {
    totalPossiblePoints,
    totalScore,
    passedCheckpoints,
    failedCheckpoints,
    scorePercentage,
    passRate,
    hasValidScoreData,
    scoreColorThreshold,
  }
}
