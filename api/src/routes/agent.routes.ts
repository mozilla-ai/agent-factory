import { Router } from 'express'
import { AgentController } from '../controllers/agent.controller.js'

const router = Router()
const agentController = new AgentController()

// Agent generation and management routes
router.post('/generate', agentController.generateAgent.bind(agentController))
router.post('/input', agentController.sendInput.bind(agentController))
router.post('/stop', agentController.stopAgent.bind(agentController))

export default router
