import type { EvaluationResults } from '../types/index.js'

export function parseEvaluationOutput(output: string): EvaluationResults {
  const results: EvaluationResults = {
    score: 0,
    maxScore: 0,
    checkpoints: [],
  }

  // Extract final score
  const scoreMatch = output.match(/Final score: (\d+(?:\.\d+)?)/)
  if (scoreMatch) {
    results.score = parseFloat(scoreMatch[1])
  }

  // Find the checkpoint results section
  const checkpointSections = output.split(/\s*Checkpoint \d+:/g)
  // Skip the first section which is the header
  if (checkpointSections.length > 1) {
    for (let i = 1; i < checkpointSections.length; i++) {
      const section = checkpointSections[i]

      // Extract the parts
      const criteriaMatch = section.match(
        /Criteria: (.*?)(?=\s*Criteria Points:)/s,
      )
      const pointsMatch = section.match(/Criteria Points: (\d+)/)
      const passedMatch = section.match(/Passed: (True|False)/)
      const reasonMatch = section.match(
        /Reason: (.*?)(?=\s*(?:Checkpoint \d+:|$))/s,
      )

      if (criteriaMatch && pointsMatch && passedMatch && reasonMatch) {
        const criteria = criteriaMatch[1].trim()
        const points = parseInt(pointsMatch[1], 10)
        const passed = passedMatch[1] === 'True'
        const reason = reasonMatch[1].trim()

        results.maxScore += points

        results.checkpoints.push({
          criteria,
          points,
          result: passed ? 'pass' : 'fail',
          feedback: reason,
        })
      }
    }
  }

  return results
}
