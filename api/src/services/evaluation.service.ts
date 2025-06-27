import fs from 'fs/promises'
import path from 'path'
import { fileService } from './file.service.js'
import { processService } from './process.service.js'
import { getWorkflowPath } from '../config/index.js'
import type { EvaluationCriteria, OutputCallback } from '../types/index.js'

export class EvaluationService {
  async runAgent(
    workflowPath: string,
    outputCallback: OutputCallback,
  ): Promise<void> {
    const workflowDir = getWorkflowPath(workflowPath)
    const agentPath = path.join(workflowDir, 'agent.py')

    // Check if agent exists
    if (!(await fileService.fileExists(agentPath))) {
      throw new Error(`Agent not found at path: ${workflowPath}/agent.py`)
    }

    // Delete existing evaluation results since agent run invalidates them
    const resultsPath = path.join(workflowDir, 'evaluation_results.json')
    if (await fileService.fileExists(resultsPath)) {
      try {
        await fileService.deleteFile(resultsPath)
        console.log(`Deleted stale evaluation results: ${resultsPath}`)
      } catch (error) {
        console.warn(`Failed to delete stale evaluation results: ${error}`)
      }
    }

    await processService.runPythonScript(agentPath, [], outputCallback)
  }

  async generateEvaluationCases(
    workflowPath: string,
    outputCallback: OutputCallback,
  ): Promise<void> {
    const workflowDir = getWorkflowPath(workflowPath)

    // Ensure workflow directory exists
    if (!(await fileService.fileExists(workflowDir))) {
      throw new Error(`Workflow not found: ${workflowPath}`)
    }

    // Delete existing evaluation results since new criteria invalidate them
    const resultsPath = path.join(workflowDir, 'evaluation_results.json')
    if (await fileService.fileExists(resultsPath)) {
      try {
        await fileService.deleteFile(resultsPath)
        console.log(`Deleted stale evaluation results: ${resultsPath}`)
      } catch (error) {
        console.warn(`Failed to delete stale evaluation results: ${error}`)
      }
    }

    await processService.runPythonScript(
      'eval/generate_evaluation_case.py',
      [`generated_workflows/${workflowPath}`],
      outputCallback,
    )
  }

  async runEvaluation(
    workflowPath: string,
    outputCallback: OutputCallback,
  ): Promise<void> {
    const workflowDir = getWorkflowPath(workflowPath)
    const agentTracePath = path.join(workflowDir, 'agent_eval_trace.json')
    const evaluationCasePath = path.join(workflowDir, 'evaluation_case.json')
    const evaluationResultsPath = path.join(
      workflowDir,
      'evaluation_results.json',
    )

    // Validate required files exist
    if (!(await fileService.fileExists(agentTracePath))) {
      throw new Error(
        'Agent trace file not found. Make sure to run the agent first.',
      )
    }

    if (!(await fileService.fileExists(evaluationCasePath))) {
      throw new Error(
        'Evaluation cases not found. Make sure to generate evaluation cases first.',
      )
    }

    const env = {
      ...process.env,
    }

    await processService.runPythonScript(
      '-m',
      [
        'eval.run_generated_agent_evaluation',
        evaluationCasePath,
        agentTracePath,
        evaluationResultsPath,
      ],
      outputCallback,
      env,
    )
  }

  async saveEvaluationCriteria(
    workflowPath: string,
    criteria: EvaluationCriteria,
  ): Promise<string> {
    const workflowDir = getWorkflowPath(workflowPath)

    // Ensure points are numbers (in case frontend sends strings)
    const normalizedCriteria: EvaluationCriteria = {
      ...criteria,
      checkpoints: criteria.checkpoints.map((checkpoint) => ({
        ...checkpoint,
        points:
          typeof checkpoint.points === 'string'
            ? Number(checkpoint.points)
            : checkpoint.points,
      })),
    }

    // Delete existing evaluation results since criteria changes invalidate them
    const resultsPath = path.join(workflowDir, 'evaluation_results.json')
    if (await fileService.fileExists(resultsPath)) {
      try {
        await fileService.deleteFile(resultsPath)
        console.log(
          `Deleted stale evaluation results due to criteria update: ${resultsPath}`,
        )
      } catch (error) {
        console.warn(`Failed to delete stale evaluation results: ${error}`)
      }
    }

    return fileService.saveEvaluationCriteria(workflowPath, normalizedCriteria)
  }

  async deleteAgentTrace(workflowPath: string): Promise<boolean> {
    return fileService.deleteAgentTrace(workflowPath)
  }

  async deleteEvaluationCriteria(workflowPath: string): Promise<boolean> {
    return fileService.deleteEvaluationCriteria(workflowPath)
  }

  async deleteEvaluationResults(workflowPath: string): Promise<boolean> {
    return fileService.deleteEvaluationResults(workflowPath)
  }

  async runAgentGeneration(
    workflowPath: string,
    criteria: EvaluationCriteria,
    onOutput?: OutputCallback,
  ): Promise<void> {
    const workflowDir = getWorkflowPath(workflowPath)

    // Ensure workflow directory exists
    if (!(await fileService.fileExists(workflowDir))) {
      throw new Error(`Workflow not found: ${workflowPath}`)
    }

    // Save criteria first
    try {
      await fileService.saveEvaluationCriteria(workflowPath, criteria)
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      console.error('Failed to save evaluation criteria:', error)
      throw new Error(`Failed to save evaluation criteria: ${errorMessage}`)
    }

    // Run agent generation using process service
    const { processService } = await import('./process.service.js')
    await processService.runAgentGeneration(workflowPath, onOutput)
  }

  async validateEvaluationFiles(workflowPath: string): Promise<void> {
    const workflowDir = getWorkflowPath(workflowPath)
    const agentTracePath = path.join(workflowDir, 'agent_eval_trace.json')
    const evaluationCasePath = path.join(workflowDir, 'evaluation_case.json')

    // Validate required files exist
    if (!(await fileService.fileExists(agentTracePath))) {
      throw new Error(
        'Agent trace file not found. Make sure to run the agent first.',
      )
    }

    if (!(await fileService.fileExists(evaluationCasePath))) {
      throw new Error(
        'Evaluation cases not found. Make sure to generate evaluation cases first.',
      )
    }
  }

  async runActualEvaluation(
    workflowPath: string,
    onOutput?: OutputCallback,
  ): Promise<void> {
    // This runs the actual evaluation script that compares agent output against criteria
    const { processService } = await import('./process.service.js')
    await processService.runAgentEvaluation(workflowPath, onOutput)
  }

  async validateEvaluationRequest(workflowPath: string): Promise<void> {
    const fullPath = getWorkflowPath(workflowPath)

    // Check if workflow directory exists
    try {
      await fs.access(fullPath)
    } catch {
      throw new Error(
        `Workflow not found: ${workflowPath}. Please ensure the workflow exists before running evaluation.`,
      )
    }

    // Check for required files
    const agentPath = path.join(fullPath, 'agent.py')
    const tracePath = path.join(fullPath, 'agent_factory_trace.json')

    try {
      await fs.access(agentPath)
    } catch {
      throw new Error(
        `Agent file (agent.py) not found in workflow: ${workflowPath}. Please generate the agent first.`,
      )
    }

    try {
      await fs.access(tracePath)
    } catch {
      throw new Error(`Workflow not found: ${workflowPath}`)
    }

    // Check for evaluation criteria (JSON format only)
    const criteriaPath = path.join(fullPath, 'evaluation_case.json')
    try {
      await fs.access(criteriaPath)
    } catch {
      throw new Error(
        `Evaluation criteria not found for workflow: ${workflowPath}. Please create evaluation criteria first.`,
      )
    }
  }
}

export const evaluationService = new EvaluationService()
