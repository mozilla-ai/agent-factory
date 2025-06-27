import { Request, Response } from 'express'
import { fileService } from '../services/file.service.js'

export class WorkflowController {
  // List all workflows
  async listWorkflows(req: Request, res: Response): Promise<void> {
    try {
      const workflows = await fileService.listWorkflows()
      res.json(workflows)
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      res.status(500).json({
        success: false,
        error: `Failed to list workflows: ${errorMessage}`,
      })
    }
  }

  // Get workflow details
  async getWorkflowDetails(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      const workflowInfo = await fileService.getWorkflowInfo(workflowPath)
      res.json(workflowInfo)
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      // If the error message indicates not found, return 404, otherwise 500
      const status = errorMessage.includes('not found') ? 404 : 500
      res.status(status).json({
        success: false,
        error: errorMessage,
      })
    }
  }

  // Get evaluation criteria
  async getEvaluationCriteria(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      const criteria = await fileService.loadEvaluationCriteria(workflowPath)
      res.json(criteria)
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      // If the error message indicates not found, return 404, otherwise 500
      const status = errorMessage.includes('not found') ? 404 : 500
      res.status(status).json({
        success: false,
        error: errorMessage,
      })
    }
  }

  // Get evaluation results
  async getEvaluationResults(req: Request, res: Response): Promise<void> {
    const { workflowPath } = req.params

    try {
      const results = await fileService.loadEvaluationResults(workflowPath)
      res.json(results)
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      // If the error message indicates not found, return 404, otherwise 500
      const status = errorMessage.includes('not found') ? 404 : 500
      res.status(status).json({
        success: false,
        error: errorMessage,
      })
    }
  }
}
