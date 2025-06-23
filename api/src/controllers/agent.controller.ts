import { Request, Response } from 'express'
import { processService } from '../services/process.service.js'
import { PROCESS_IDS, MESSAGES, DEFAULTS } from '../constants/index.js'
import {
  handleStreamingError,
  setupStreamingResponse,
  completeStreamingResponse,
} from '../utils/streaming.utils.js'

export class AgentController {
  // Generate agent
  async generateAgent(req: Request, res: Response): Promise<void> {
    const { prompt = DEFAULTS.AGENT_PROMPT } = req.body

    try {
      setupStreamingResponse(res)

      const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
        const prefix = source === 'stderr' ? '[ERROR] ' : ''
        res.write(`${prefix}${text}`)
      }

      await processService.runAgentFactory(prompt, outputCallback)
      completeStreamingResponse(res, MESSAGES.SUCCESS.AGENT_COMPLETED)
    } catch (error) {
      handleStreamingError(res, error, '[agent-factory] Workflow failed')
    }
  }

  // Send input to running agent
  async sendInput(req: Request, res: Response): Promise<void> {
    const { input } = req.body

    const success = processService.sendInput(PROCESS_IDS.AGENT_FACTORY, input)

    res.json({
      success,
      message: success
        ? 'Input sent to agent process'
        : 'No running agent process found',
    })
  }

  // Stop running agent
  async stopAgent(req: Request, res: Response): Promise<void> {
    const success = processService.stopProcess(PROCESS_IDS.AGENT_FACTORY)

    res.json({
      success: true,
      message: success
        ? 'Agent process stopped'
        : 'No running agent process found',
    })
  }
}
