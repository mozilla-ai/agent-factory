import { Request, Response } from 'express'
import { asyncHandler } from '../middleware/error.middleware.js'
import { setupStreamingResponse, completeStreamingResponse } from '../utils/streaming.utils.js'
import { evaluationService } from '../services/evaluation.service.js'
import { fileService } from '../services/file.service.js'
import { processService } from '../services/process.service.js'
import type { OutputCallback } from '../types/index.js'

export class EvaluationController {
  // Run agent evaluation
  runAgent = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { workflowPath } = req.params

    setupStreamingResponse(res)

    const outputCallback: OutputCallback = (source, text) => {
      res.write(text)
    }

    await evaluationService.runEvaluation(workflowPath, outputCallback)

    completeStreamingResponse(res, '[Agent run completed. Generated agent_eval_trace.json]')
  })

  // Generate evaluation cases
  generateEvaluationCases = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { workflowPath } = req.params
    const criteria = req.body

    setupStreamingResponse(res)

    const outputCallback: OutputCallback = (source, text) => {
      res.write(text)
    }

    await evaluationService.runAgentGeneration(workflowPath, criteria, outputCallback)

    completeStreamingResponse(
      res,
      '[Evaluation cases generation completed. Saved to evaluation_case.yaml]',
    )
  })

  // Run evaluation
  runEvaluation = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { workflowPath } = req.params

    setupStreamingResponse(res)

    const outputCallback: OutputCallback = (source, text) => {
      res.write(text)
    }

    await evaluationService.validateEvaluationFiles(workflowPath)
    await processService.runAgentEvaluation(workflowPath, outputCallback)

    completeStreamingResponse(res, '[Agent evaluation completed. Results saved to evaluation_results.json]')
  })

  // Save evaluation criteria
  saveEvaluationCriteria = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { workflowPath } = req.params
    const criteria = req.body

    const filePath = await fileService.saveEvaluationCriteria(workflowPath, criteria)

    res.json({
      success: true,
      message: 'Evaluation criteria saved successfully',
      path: filePath,
    })
  })

  // Delete agent evaluation trace
  deleteAgentTrace = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { workflowPath } = req.params

    const success = await fileService.deleteAgentTrace(workflowPath)

    if (success) {
      res.json({ success: true, message: 'Agent trace deleted successfully' })
    } else {
      res.status(404).json({ error: 'Agent trace file not found' })
    }
  })

  // Delete evaluation criteria
  deleteEvaluationCriteria = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { workflowPath } = req.params

    const success = await fileService.deleteEvaluationCriteria(workflowPath)

    if (success) {
      res.json({ success: true, message: 'Evaluation criteria deleted successfully' })
    } else {
      res.status(404).json({ error: 'Evaluation criteria file not found' })
    }
  })

  // Delete evaluation results
  deleteEvaluationResults = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { workflowPath } = req.params

    const success = await fileService.deleteEvaluationResults(workflowPath)

    if (success) {
      res.json({ success: true, message: 'Evaluation results deleted successfully' })
    } else {
      res.status(404).json({ error: 'Evaluation results file not found' })
    }
  })
}

export const evaluationController = new EvaluationController()
