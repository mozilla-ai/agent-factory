import { Request, Response } from 'express'
import { asyncHandler } from '../middleware/error.middleware.js'
import {
  setupStreamingResponse,
  completeStreamingResponse,
  handleStreamingError,
} from '../utils/streaming.utils.js'
import { evaluationService } from '../services/evaluation.service.js'
import { fileService } from '../services/file.service.js'
import type { OutputCallback } from '../types/index.js'

export class EvaluationController {
  // Run agent evaluation (Step 1: Run the agent.py file)
  runAgent = asyncHandler(
    async (req: Request, res: Response): Promise<void> => {
      const { workflowPath } = req.params

      setupStreamingResponse(res)

      const outputCallback: OutputCallback = (source, text) => {
        res.write(text)
      }

      try {
        await evaluationService.runAgent(workflowPath, outputCallback)
        completeStreamingResponse(
          res,
          '[Agent run completed. Generated agent_eval_trace.json]',
        )
      } catch (error) {
        handleStreamingError(res, error, 'Failed to run agent')
      }
    },
  )

  // Generate evaluation cases (Step 2: Auto-generate criteria using Python script)
  generateEvaluationCases = asyncHandler(
    async (req: Request, res: Response): Promise<void> => {
      const { workflowPath } = req.params

      setupStreamingResponse(res)

      const outputCallback: OutputCallback = (source, text) => {
        res.write(text)
      }

      try {
        console.log(
          `Auto-generating evaluation cases for workflow: ${workflowPath}`,
        )

        // Generate evaluation cases using Python script
        await evaluationService.generateEvaluationCases(
          workflowPath,
          outputCallback,
        )
        completeStreamingResponse(
          res,
          '[Evaluation cases generation completed. Saved to evaluation_case.yaml]',
        )
      } catch (error) {
        handleStreamingError(res, error, 'Failed to generate evaluation cases')
      }
    },
  )

  // Run evaluation (Step 3: Run the actual evaluation comparing agent vs criteria)
  runEvaluation = asyncHandler(
    async (req: Request, res: Response): Promise<void> => {
      const { workflowPath } = req.params

      setupStreamingResponse(res)

      const outputCallback: OutputCallback = (source, text) => {
        res.write(text)
      }

      try {
        await evaluationService.runEvaluation(workflowPath, outputCallback)
        completeStreamingResponse(
          res,
          '[Agent evaluation completed. Results saved to evaluation_results.json]',
        )
      } catch (error) {
        handleStreamingError(res, error, 'Failed to run evaluation')
      }
    },
  )

  // Save evaluation criteria
  saveEvaluationCriteria = asyncHandler(
    async (req: Request, res: Response): Promise<void> => {
      const { workflowPath } = req.params
      const criteria = req.body

      const filePath = await fileService.saveEvaluationCriteria(
        workflowPath,
        criteria,
      )

      res.json({
        success: true,
        message: 'Evaluation criteria saved successfully',
        path: filePath,
      })
    },
  )

  // Delete agent evaluation trace
  deleteAgentTrace = asyncHandler(
    async (req: Request, res: Response): Promise<void> => {
      const { workflowPath } = req.params

      const success = await fileService.deleteAgentTrace(workflowPath)

      if (success) {
        res.json({
          success: true,
          message:
            'Agent trace deleted successfully (evaluation results also invalidated if they existed)',
        })
      } else {
        res.status(404).json({ error: 'Agent trace file not found' })
      }
    },
  )

  // Delete evaluation criteria
  deleteEvaluationCriteria = asyncHandler(
    async (req: Request, res: Response): Promise<void> => {
      const { workflowPath } = req.params

      const success = await fileService.deleteEvaluationCriteria(workflowPath)

      if (success) {
        res.json({
          success: true,
          message:
            'Evaluation criteria deleted successfully (evaluation results also invalidated if they existed)',
        })
      } else {
        res.status(404).json({ error: 'Evaluation criteria file not found' })
      }
    },
  )

  // Delete evaluation results
  deleteEvaluationResults = asyncHandler(
    async (req: Request, res: Response): Promise<void> => {
      const { workflowPath } = req.params

      const success = await fileService.deleteEvaluationResults(workflowPath)

      if (success) {
        res.json({
          success: true,
          message: 'Evaluation results deleted successfully',
        })
      } else {
        res.status(404).json({ error: 'Evaluation results file not found' })
      }
    },
  )
}

export const evaluationController = new EvaluationController()
