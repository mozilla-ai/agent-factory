import { Request, Response } from 'express'
import { runAgentFactoryWorkflowWithStreaming } from '../helpers/agent-factory-helpers.js'

// Run agent factory workflow
export async function generateAgent(req: Request, res: Response) {
  res.setHeader('Content-Type', 'text/plain; charset=utf-8')
  const prompt =
    (req.query.prompt as string) ||
    'Summarize text content from a given webpage URL'

  try {
    await runAgentFactoryWorkflowWithStreaming(
      prompt,
      (source: 'stdout' | 'stderr', text: string) => {
        if (source === 'stdout') {
          console.log(`${text}`)
          res.write(`${text}`)
        } else if (source === 'stderr') {
          console.log(`${text}`)
          res.write(`${text}`)
        }
      },
    )
    res.end('\n[agent-factory] Workflow completed successfully.')
  } catch (error: unknown) {
    console.error('Error during agent factory workflow:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).send(`[agent-factory] Workflow failed: ${errorMessage}`)
  }
}
