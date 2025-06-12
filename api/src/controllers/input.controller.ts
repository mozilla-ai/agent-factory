import { Request, Response } from 'express'
import {
  getRunningPythonProcess,
  stopRunningPythonProcess,
} from '../helpers/agent-factory-helpers.js'

// Send input to running Python process
export function sendInput(req: Request, res: Response) {
  const { input } = req.body as { input: string }
  const proc = getRunningPythonProcess()

  if (!proc) {
    res.status(400).send('No running Python process')
  } else {
    proc.stdin.write(`${input}\n`)
    res.send('Input sent to Python process')
  }
}

// Stop running Python process
export function stopPythonProcess(_req: Request, res: Response) {
  stopRunningPythonProcess()
  res.send('Python process stopped')
}
