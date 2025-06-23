import { Request, Response } from 'express'
import { evaluationService } from '../services/evaluation.service.js'
import { MESSAGES } from '../constants/index.js'
import {
  handleStreamingError,
  setupStreamingResponse,
  completeStreamingResponse,
} from '../utils/streaming.utils.js'

export class EvaluationController {
  // Run agent for evaluation
  async runAgent(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      setupStreamingResponse(res)

      const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
        const prefix = source === 'stderr' ? '[ERROR] ' : ''
        res.write(`${prefix}${text}`)
      }

      await evaluationService.runAgent(workflowPath, outputCallback)
      completeStreamingResponse(res, MESSAGES.SUCCESS.AGENT_RUN_COMPLETED)
    } catch (error) {
      handleStreamingError(res, error, 'Failed to run agent')
    }
  }

  // Generate evaluation cases
  async generateEvaluationCases(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      setupStreamingResponse(res)

      const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
        const prefix = source === 'stderr' ? '[ERROR] ' : ''
        res.write(`${prefix}${text}`)
      }

      await evaluationService.generateEvaluationCases(
        workflowPath,
        outputCallback,
      )
      completeStreamingResponse(
        res,
        MESSAGES.SUCCESS.EVALUATION_CASES_COMPLETED,
      )
    } catch (error) {
      handleStreamingError(res, error, 'Failed to generate evaluation cases')
    }
  }

  // Run evaluation
  async runEvaluation(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      setupStreamingResponse(res)

      const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
        const prefix = source === 'stderr' ? '[ERROR] ' : ''
        res.write(`${prefix}${text}`)
      }

      await evaluationService.runEvaluation(workflowPath, outputCallback)
      completeStreamingResponse(res, MESSAGES.SUCCESS.EVALUATION_COMPLETED)
    } catch (error) {
      handleStreamingError(res, error, 'Failed to run evaluation')
    }
  }

  // Save evaluation criteria
  async saveEvaluationCriteria(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params
    const criteria = req.body

    try {
      const filePath = await evaluationService.saveEvaluationCriteria(
        workflowPath,
        criteria,
      )
      res.json({
        success: true,
        data: { path: filePath },
        message: 'Evaluation criteria saved successfully',
      })
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      res.status(500).json({
        success: false,
        error: `Failed to save evaluation criteria: ${errorMessage}`,
      })
    }
  }

  // Delete agent evaluation trace
  async deleteAgentTrace(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      const deleted = await evaluationService.deleteAgentTrace(workflowPath)
      res.json({
        success: deleted,
        message: deleted
          ? 'Agent evaluation trace deleted successfully'
          : 'Agent evaluation trace file not found',
      })
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      res.status(500).json({
        success: false,
        error: `Failed to delete agent trace: ${errorMessage}`,
      })
    }
  }

  // Delete evaluation criteria
  async deleteEvaluationCriteria(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      const deleted =
        await evaluationService.deleteEvaluationCriteria(workflowPath)
      res.json({
        success: deleted,
        message: deleted
          ? 'Evaluation criteria deleted successfully'
          : 'Evaluation criteria file not found',
      })
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      res.status(500).json({
        success: false,
        error: `Failed to delete evaluation criteria: ${errorMessage}`,
      })
    }
  }

  // Delete evaluation results
  async deleteEvaluationResults(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      const deleted =
        await evaluationService.deleteEvaluationResults(workflowPath)
      res.json({
        success: deleted,
        message: deleted
          ? 'Evaluation results deleted successfully'
          : 'Evaluation results file not found',
      })
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      res.status(500).json({
        success: false,
        error: `Failed to delete evaluation results: ${errorMessage}`,
      })
    }
  }
}
