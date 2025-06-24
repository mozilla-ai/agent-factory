import path from 'path'
import { processService } from './process.service.js'
import { fileService } from './file.service.js'
import { getWorkflowPath } from '../config/index.js'
import { NotFoundError } from '../middleware/error.middleware.js'
import { MESSAGES, FILE_NAMES } from '../constants/index.js'
import type { EvaluationCriteria, OutputCallback } from '../types/index.js'

export class EvaluationService {
  async runAgent(
    workflowPath: string,
    outputCallback: OutputCallback,
  ): Promise<void> {
    const workflowDir = getWorkflowPath(workflowPath)
    const agentPath = path.join(workflowDir, FILE_NAMES.AGENT)

    // Check if agent exists
    if (!(await fileService.fileExists(agentPath))) {
      throw new NotFoundError(
        `Agent not found at path: ${workflowPath}/agent.py`,
      )
    }

    await processService.runPythonScript(agentPath, [], outputCallback)

    // Copy trace file from latest to workflow directory if needed
    await this.copyTraceFileIfNeeded(workflowPath)
  }

  async generateEvaluationCases(
    workflowPath: string,
    outputCallback: OutputCallback,
  ): Promise<void> {
    const workflowDir = getWorkflowPath(workflowPath)

    // Ensure workflow directory exists
    if (!(await fileService.fileExists(workflowDir))) {
      throw new NotFoundError(`Workflow not found: ${workflowPath}`)
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
    const agentTracePath = path.join(workflowDir, FILE_NAMES.AGENT_EVAL_TRACE)
    const evaluationCasePath = path.join(
      workflowDir,
      FILE_NAMES.EVALUATION_CASE,
    )
    const evaluationResultsPath = path.join(
      workflowDir,
      FILE_NAMES.EVALUATION_RESULTS,
    )

    // Validate required files exist
    if (!(await fileService.fileExists(agentTracePath))) {
      throw new NotFoundError(MESSAGES.ERROR.AGENT_TRACE_NOT_FOUND)
    }

    if (!(await fileService.fileExists(evaluationCasePath))) {
      throw new NotFoundError(MESSAGES.ERROR.EVALUATION_CASES_NOT_FOUND)
    }

    const env = {
      ...process.env,
      AGENT_PATH: workflowDir,
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
    return fileService.saveEvaluationCriteria(workflowPath, criteria)
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

  // Private helper to copy trace file if needed
  private async copyTraceFileIfNeeded(workflowPath: string): Promise<void> {
    try {
      const latestWorkflowDir = getWorkflowPath('latest')
      const workflowDir = getWorkflowPath(workflowPath)

      const sourceTracePath = path.join(
        latestWorkflowDir,
        FILE_NAMES.AGENT_EVAL_TRACE,
      )
      const targetTracePath = path.join(
        workflowDir,
        FILE_NAMES.AGENT_EVAL_TRACE,
      )

      if (await fileService.fileExists(sourceTracePath)) {
        await fileService.copyFile(sourceTracePath, targetTracePath)
        console.log(`Copied agent trace from latest to ${workflowPath}`)
      }
    } catch (error) {
      console.warn('Could not copy trace file from latest workflow:', error)
      // Don't throw here as the main operation succeeded
    }
  }
}

// Singleton instance
export const evaluationService = new EvaluationService()
