<!-- filepath: /Users/khaled/github/agent-factory/ui/src/components/EvaluationCriteriaViewer.vue -->
<template>
  <!-- Fix reactive property access in conditionals -->
  <div class="evaluation-criteria-viewer">
    <div v-if="criteriaQuery.isPending.value" class="criteria-loading">
      Loading evaluation criteria...
    </div>
    <div v-else-if="criteriaQuery.isError.value" class="criteria-error">
      {{
        criteriaQuery.error.value instanceof Error
          ? criteriaQuery.error.value.message
          : 'Error loading criteria'
      }}
    </div>
    <div v-else-if="!criteriaQuery.data.value" class="criteria-empty">
      No evaluation criteria available
    </div>

    <div v-else class="criteria-content">
      <!-- Header with judge info -->
      <div class="criteria-header">
        <h3>Evaluation Criteria</h3>
        <div class="judge-info">
          <span class="judge-label">LLM Judge:</span>
          <span class="judge-model">{{ criteriaQuery.data.value.llm_judge }}</span>
        </div>
        <div class="points-summary">
          <span class="points-label">Total Points Possible:</span>
          <span class="points-value">{{ totalPossiblePoints }}</span>
        </div>
      </div>

      <!-- Criteria checklist -->
      <div class="criteria-checklist">
        <div
          v-for="(checkpoint, index) in criteriaQuery.data.value.checkpoints"
          :key="index"
          class="checkpoint-item"
        >
          <div class="checkpoint-header">
            <div class="checkpoint-number">{{ index + 1 }}</div>
            <div class="checkpoint-content">
              <div class="checkpoint-criteria">{{ checkpoint.criteria }}</div>
              <div class="checkpoint-points">
                {{ checkpoint.points }} {{ checkpoint.points === 1 ? 'point' : 'points' }}
              </div>
            </div>
          </div>

          <div v-if="hasResults" class="checkpoint-result">
            <div
              class="result-indicator"
              :class="{
                'result-pass': evaluationResults[index]?.result === 'pass',
                'result-fail': evaluationResults[index]?.result === 'fail',
              }"
            >
              <span v-if="evaluationResults[index]?.result === 'pass'">✓</span>
              <span v-else-if="evaluationResults[index]?.result === 'fail'">✗</span>
              <span v-else>N/A</span>
            </div>
            <div v-if="evaluationResults[index]?.feedback" class="result-feedback">
              {{ evaluationResults[index]?.feedback }}
            </div>
          </div>
        </div>
      </div>

      <!-- Final score (if results available) -->
      <div class="final-score">
        <h3>Final Score</h3>
        <div class="score-display">
          <div class="score-value">{{ totalScore }} / {{ totalPossiblePoints }}</div>
          <div class="score-percentage">
            {{ Math.round((totalScore / totalPossiblePoints) * 100) }}%
          </div>
        </div>
        <div class="score-bar">
          <div
            class="score-progress"
            :style="{ width: `${(totalScore / totalPossiblePoints) * 100}%` }"
            :class="{
              'score-high': totalScore / totalPossiblePoints >= 0.8,
              'score-medium':
                totalScore / totalPossiblePoints >= 0.5 && totalScore / totalPossiblePoints < 0.8,
              'score-low': totalScore / totalPossiblePoints < 0.5,
            }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import yaml from 'js-yaml'
import { useQuery } from '@tanstack/vue-query'

// Props
const props = defineProps<{
  workflowPath: string
}>()

// Fetch evaluation criteria
const criteriaQuery = useQuery({
  queryKey: ['evaluation-criteria', props.workflowPath],
  queryFn: async () => {
    const response = await fetch(
      `http://localhost:3000/agent-factory/workflows/${props.workflowPath}/evaluation_case.yaml`,
    )

    if (!response.ok) {
      throw new Error(
        `Failed to load evaluation criteria: ${response.status} ${response.statusText}`,
      )
    }

    const criteriaText = await response.text()
    return yaml.load(criteriaText) as {
      llm_judge: string
      checkpoints: Array<{
        criteria: string
        points: number
      }>
    }
  },
})

// Fetch evaluation results
const resultsQuery = useQuery({
  queryKey: ['evaluation-results', props.workflowPath],
  queryFn: async () => {
    const response = await fetch(
      `http://localhost:3000/agent-factory/workflows/${props.workflowPath}/evaluation_results.json`,
    )

    if (!response.ok) {
      // If no results yet, we don't throw an error
      // This is expected when results haven't been generated
      return { checkpoints: [] }
    }

    return response.json()
  },
  // No need to wait for criteria to load to fetch results
  enabled: computed(() => !!props.workflowPath),
  // Don't retry too many times for results that might not exist yet
  retry: 1,
})

// Prepare evaluation results with proper alignment to criteria
const evaluationResults = computed(() => {
  if (!resultsQuery.data.value || !criteriaQuery.data.value) {
    return []
  }

  const results = resultsQuery.data.value.checkpoints || []

  // Ensure we have a result for each criterion
  if (criteriaQuery.data.value.checkpoints.length > results.length) {
    // Pad with empty results if needed
    const missing = criteriaQuery.data.value.checkpoints.length - results.length
    for (let i = 0; i < missing; i++) {
      results.push({ result: null })
    }
  }

  return results
})

// Check if evaluation results are available
const hasResults = computed(() => {
  return resultsQuery.data.value?.checkpoints?.length > 0
})

// Calculate total possible points
const totalPossiblePoints = computed(() => {
  if (!criteriaQuery.data.value || !criteriaQuery.data.value.checkpoints) return 0
  return criteriaQuery.data.value.checkpoints.reduce(
    (sum: number, checkpoint: any) => sum + checkpoint.points,
    0,
  )
})

// Calculate total score from results
const totalScore = computed(() => {
  if (!hasResults.value) return 0
  return evaluationResults.value.reduce((sum: number, result: any, index: number) => {
    // Fix this line to use .value when accessing criteriaQuery.data
    const points = criteriaQuery.data.value?.checkpoints[index]?.points || 0
    return sum + (result.result === 'pass' ? points : 0)
  }, 0)
})
</script>

<style scoped>
.evaluation-criteria-viewer {
  padding: 1rem;
}

.criteria-loading,
.criteria-error,
.criteria-empty {
  text-align: center;
  padding: 2rem;
  font-size: 1.1rem;
}

.criteria-error {
  color: var(--color-error, #e74c3c);
}

.criteria-header {
  background-color: var(--color-background-soft);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.judge-info {
  margin: 0.5rem 0;
}

.judge-label,
.points-label {
  font-weight: 500;
  margin-right: 0.5rem;
}

.judge-model {
  background-color: var(--color-background);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
}

.points-value {
  font-weight: 500;
}

.criteria-checklist {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.checkpoint-item {
  background-color: var(--color-background-soft);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.checkpoint-header {
  display: flex;
  padding: 1rem;
  background-color: var(--color-background-soft);
  border-bottom: 1px solid var(--color-border);
}

.checkpoint-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  background-color: var(--color-background);
  border-radius: 50%;
  font-weight: bold;
  margin-right: 1rem;
  border: 1px solid var(--color-border);
}

.checkpoint-content {
  flex: 1;
}

.checkpoint-criteria {
  margin-bottom: 0.5rem;
}

.checkpoint-points {
  font-size: 0.9rem;
  color: var(--color-text-light, var(--color-text-secondary));
  font-weight: 500;
}

.checkpoint-result {
  display: flex;
  padding: 1rem;
  background-color: var(--color-background);
  border-top: 1px solid var(--color-border);
}

.result-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  font-weight: bold;
  margin-right: 1rem;
  font-size: 1.2rem;
}

.result-pass {
  background-color: rgba(46, 204, 113, 0.15);
  color: var(--color-success, #2ecc71);
  border: 1px solid var(--color-success, #2ecc71);
}

.result-fail {
  background-color: rgba(231, 76, 60, 0.15);
  color: var(--color-error, #e74c3c);
  border: 1px solid var(--color-error, #e74c3c);
}

.result-feedback {
  flex: 1;
}

.final-score {
  background-color: var(--color-background-soft);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.score-display {
  display: flex;
  align-items: baseline;
  gap: 1rem;
  margin: 1rem 0;
}

.score-value {
  font-size: 2rem;
  font-weight: bold;
}

.score-percentage {
  font-size: 1.2rem;
  font-weight: 500;
  color: var(--color-text-light, var(--color-text-secondary));
}

.score-bar {
  height: 8px;
  background-color: var(--color-background);
  border-radius: 4px;
  overflow: hidden;
}

.score-progress {
  height: 100%;
  transition: width 0.5s ease;
}

.score-high {
  background-color: var(--color-success, #2ecc71);
}

.score-medium {
  background-color: var(--color-warning, #f39c12);
}

.score-low {
  background-color: var(--color-error, #e74c3c);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .checkpoint-header {
    flex-direction: column;
  }

  .checkpoint-number {
    margin-bottom: 0.5rem;
  }
}
</style>
