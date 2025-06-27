import { Router } from 'express'
import { EvaluationController } from '../controllers/evaluation.controller.js'

const router = Router()
const evaluationController = new EvaluationController()

// Evaluation routes
router.post(
  '/:workflowPath/run-agent',
  evaluationController.runAgent.bind(evaluationController),
)
router.post(
  '/:workflowPath/generate-cases',
  evaluationController.generateEvaluationCases.bind(evaluationController),
)
router.post(
  '/:workflowPath/run-evaluation',
  evaluationController.runEvaluation.bind(evaluationController),
)
router.post(
  '/:workflowPath/criteria',
  evaluationController.saveEvaluationCriteria.bind(evaluationController),
)

// Delete routes
router.delete(
  '/:workflowPath/trace',
  evaluationController.deleteAgentTrace.bind(evaluationController),
)
router.delete(
  '/:workflowPath/criteria',
  evaluationController.deleteEvaluationCriteria.bind(evaluationController),
)
router.delete(
  '/:workflowPath/results',
  evaluationController.deleteEvaluationResults.bind(evaluationController),
)

export default router
