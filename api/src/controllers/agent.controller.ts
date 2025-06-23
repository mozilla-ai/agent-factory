import { Request, Response } from 'express'
import { processService } from '../services/process.service.js'
import { PROCESS_IDS, MESSAGES, DEFAULTS } from '../constants/index.js'

export class AgentController {
  // Generate agent
  async generateAgent(req: Request, res: Response): Promise<void> {
    const { prompt = DEFAULTS.AGENT_PROMPT } = req.body

    try {
      res.setHeader('Content-Type', 'text/plain')
      res.setHeader('Cache-Control', 'no-cache')
      res.setHeader('Connection', 'keep-alive')

      const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
        const prefix = source === 'stderr' ? '[ERROR] ' : ''
        res.write(`${prefix}${text}`)
      }

      await processService.runAgentFactory(prompt, outputCallback)
      res.write(`\n${MESSAGES.SUCCESS.AGENT_COMPLETED}\n`)
      res.end()
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)

      if (!res.headersSent) {
        // Stream hasn't started, send proper HTTP error
        res.status(500).send(`[agent-factory] Workflow failed: ${errorMessage}`)
      } else {
        // Stream is active, write error to stream and end
        res.write(`\n[FATAL ERROR] ${errorMessage}\n`)
        res.end()
      }
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
