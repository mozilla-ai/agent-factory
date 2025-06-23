import { Request, Response } from 'express'
import { evaluationService } from '../services/evaluation.service.js'
import { MESSAGES } from '../constants/index.js'

export class EvaluationController {
  // Run agent for evaluation
  async runAgent(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      res.setHeader('Content-Type', 'text/plain')
      res.setHeader('Cache-Control', 'no-cache')
      res.setHeader('Connection', 'keep-alive')

      const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
        const prefix = source === 'stderr' ? '[ERROR] ' : ''
        res.write(`${prefix}${text}`)
      }

      await evaluationService.runAgent(workflowPath, outputCallback)
      res.write(`\n${MESSAGES.SUCCESS.AGENT_RUN_COMPLETED}\n`)
      res.end()
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)

      if (!res.headersSent) {
        // Stream hasn't started, send proper HTTP error
        res.status(500).send(`Failed to run agent: ${errorMessage}`)
      } else {
        // Stream is active, write error to stream and end
        res.write(`\n[FATAL ERROR] Failed to run agent: ${errorMessage}\n`)
        res.end()
      }
    }
  }

  // Generate evaluation cases
  async generateEvaluationCases(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      res.setHeader('Content-Type', 'text/plain')
      res.setHeader('Cache-Control', 'no-cache')
      res.setHeader('Connection', 'keep-alive')

      const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
        const prefix = source === 'stderr' ? '[ERROR] ' : ''
        res.write(`${prefix}${text}`)
      }

      await evaluationService.generateEvaluationCases(
        workflowPath,
        outputCallback,
      )
      res.write(`\n${MESSAGES.SUCCESS.EVALUATION_CASES_COMPLETED}\n`)
      res.end()
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)

      if (!res.headersSent) {
        // Stream hasn't started, send proper HTTP error
        res
          .status(500)
          .send(`Failed to generate evaluation cases: ${errorMessage}`)
      } else {
        // Stream is active, write error to stream and end
        res.write(
          `\n[FATAL ERROR] Failed to generate evaluation cases: ${errorMessage}\n`,
        )
        res.end()
      }
    }
  }

  // Run evaluation
  async runEvaluation(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      res.setHeader('Content-Type', 'text/plain')
      res.setHeader('Cache-Control', 'no-cache')
      res.setHeader('Connection', 'keep-alive')

      const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
        const prefix = source === 'stderr' ? '[ERROR] ' : ''
        res.write(`${prefix}${text}`)
      }

      await evaluationService.runEvaluation(workflowPath, outputCallback)
      res.write(`\n${MESSAGES.SUCCESS.EVALUATION_COMPLETED}\n`)
      res.end()
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)

      if (!res.headersSent) {
        // Stream hasn't started, send proper HTTP error
        res.status(500).send(`Failed to run evaluation: ${errorMessage}`)
      } else {
        // Stream is active, write error to stream and end
        res.write(`\n[FATAL ERROR] Failed to run evaluation: ${errorMessage}\n`)
        res.end()
      }
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
