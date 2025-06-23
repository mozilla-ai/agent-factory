<template>
  <div class="checkpoint-item">
    <div class="checkpoint-header">
      <div class="checkpoint-number">{{ number }}</div>
      <div class="checkpoint-content">
        <div class="checkpoint-criteria">{{ criteria }}</div>
        <div class="checkpoint-points">{{ points }} {{ points === 1 ? 'point' : 'points' }}</div>
      </div>
    </div>

    <div v-if="result" class="checkpoint-result">
      <div
        class="result-indicator"
        :class="{
          'result-pass': result.result === 'pass',
          'result-fail': result.result === 'fail',
        }"
      >
        <span v-if="result.result === 'pass'">✓</span>
        <span v-else-if="result.result === 'fail'">✗</span>
        <span v-else>N/A</span>
      </div>
      <div v-if="result.feedback" class="result-feedback">
        {{ result.feedback }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface EvaluationResult {
  result: 'pass' | 'fail'
  feedback?: string
}

interface Props {
  number: number
  criteria: string
  points: number
  result?: EvaluationResult
}

defineProps<Props>()
</script>

<style scoped>
.checkpoint-item {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-background);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.checkpoint-header {
  display: flex;
  padding: 1rem;
  align-items: flex-start;
  gap: 1rem;
}

.checkpoint-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background-color: var(--color-background-soft);
  color: var(--color-text);
  font-weight: bold;
  border: 1px solid var(--color-border);
  flex-shrink: 0;
}

.checkpoint-content {
  flex: 1;
}

.checkpoint-criteria {
  font-size: 1rem;
  line-height: 1.4;
  margin-bottom: 0.5rem;
  color: var(--color-text);
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
  flex-shrink: 0;
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
  color: var(--color-text);
  line-height: 1.4;
}
</style>
