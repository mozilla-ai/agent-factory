import { Router } from 'express'
import { WorkflowController } from '../controllers/workflow.controller.js'

const router = Router()
const workflowController = new WorkflowController()

// Workflow routes
router.get('/', workflowController.listWorkflows.bind(workflowController))
router.get(
  '/:workflowPath',
  workflowController.getWorkflowDetails.bind(workflowController),
)
router.get(
  '/:workflowPath/criteria',
  workflowController.getEvaluationCriteria.bind(workflowController),
)
router.get(
  '/:workflowPath/results',
  workflowController.getEvaluationResults.bind(workflowController),
)

export default router
