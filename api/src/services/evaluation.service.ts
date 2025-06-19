import path from 'node:path'
import fs from 'node:fs/promises'
import YAML from 'yaml'
import { resolveWorkflowPath } from '../utils/path.utils.js'

export interface EvaluationCheckpoint {
  criteria: string
  points: number
}

export interface EvaluationCriteria {
  llm_judge: string
  checkpoints: EvaluationCheckpoint[]
}

export async function saveEvaluationCriteria(
  workflowPath: string,
  criteriaData: EvaluationCriteria,
): Promise<{ success: boolean; path: string }> {
  const fullPath = resolveWorkflowPath(workflowPath)

  // Convert to YAML
  const yamlContent = YAML.stringify(criteriaData)

  // Create file path
  const criteriaFilePath = path.join(fullPath, 'evaluation_case.yaml')

  // Write to file
  await fs.writeFile(criteriaFilePath, yamlContent, 'utf8')

  return {
    success: true,
    path: criteriaFilePath,
  }
}
