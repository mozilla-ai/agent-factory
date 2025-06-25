import { Request, Response } from 'express'
import { asyncHandler } from '../middleware/error.middleware.js'
import { setupStreamingResponse, completeStreamingResponse } from '../utils/streaming.utils.js'
import { processService } from '../services/process.service.js'
import type { OutputCallback } from '../types/index.js'

export class AgentController {
  // Generate agent
  generateAgent = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { prompt } = req.body

    setupStreamingResponse(res)

    // Use prompt from request body or default
    const agentPrompt = prompt || 'Summarize text content from a given webpage URL'

    const outputCallback: OutputCallback = (source, text) => {
      res.write(text)
    }

    await processService.runAgentFactory(agentPrompt, outputCallback)

    completeStreamingResponse(res, '[agent-factory] Workflow completed successfully.')
  })

  // Send input to running agent
  sendInput = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const { processId } = req.params
    const { input } = req.body

    const success = processService.sendInput(processId, input)

    if (success) {
      res.json({ success: true })
    } else {
      res.status(404).json({ error: 'Process not found or cannot send input' })
    }
  })

  // Stop running agent
  stopAgent = asyncHandler(async (req: Request, res: Response): Promise<void> => {
    const success = processService.stopProcess('agent-factory')

    if (success) {
      res.json({ success: true, message: 'Agent process stopped' })
    } else {
      res.status(404).json({ error: 'No running agent process found' })
    }
  })
}

export const agentController = new AgentController()
