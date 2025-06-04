import express, { Request, Response, NextFunction } from 'express'
import dotenv from 'dotenv'
import cors from 'cors'
import {
  runAgentFactoryWorkflowWithStreaming,
  getRunningPythonProcess,
  stopRunningPythonProcess,
} from './helpers/agent-factory-helpers.js'
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Server } from 'node:http'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Load environment variables
dotenv.config()

type FileEntry = {
  name: string
  isDirectory: boolean
  files?: FileEntry[]
}

// Create Express application
const app = express()
const PORT = process.env.PORT || 3000

// Middleware setup
app.use(express.json())
app.use(cors())
app.use(express.urlencoded({ extended: true }))

app.get('/', (_req: Request, res: Response) => {
  res.send('Hello World!')
})

// Run agent factory workflow
app.get('/agent-factory', async (req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/plain; charset=utf-8')
  const prompt = (req.query.prompt as string) || 'Summarize text content from a given webpage URL'

  try {
    await runAgentFactoryWorkflowWithStreaming(prompt, (source: 'stdout' | 'stderr', text: string) => {
      if (source === 'stdout') {
        res.write(`[agent-factory stdout]: ${text}`)
      } else if (source === 'stderr') {
        res.write(`[agent-factory stderr]: ${text}`)
      }
    })
    res.end('\n[agent-factory] Workflow completed successfully.')
  } catch (error: unknown) {
    console.error('Error during agent factory workflow:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).send(`[agent-factory] Workflow failed: ${errorMessage}`)
  }
})

// Send input to running Python process
app.post('/agent-factory/input', (req: Request, res: Response) => {
  const { input } = req.body as { input: string }
  const proc = getRunningPythonProcess()

  if (!proc) {
    res.status(400).send('No running Python process')
  } else {
    proc.stdin.write(`${input}\n`)
    res.send('Input sent to Python process')
  }
})

// Stop running Python process
app.post('/agent-factory/stop', (_req: Request, res: Response) => {
  stopRunningPythonProcess()
  res.send('Python process stopped')
})

/**
 * Helper to recursively list files and directories asynchronously
 * @param dirPath - Directory path to list
 * @returns List of files and directories with their metadata
 */
async function listFilesRecursive(dirPath: string): Promise<FileEntry[]> {
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true })

    return Promise.all(
      entries.map(async (entry) => {
        const fullPath = path.join(dirPath, entry.name)

        if (entry.isDirectory()) {
          return {
            name: entry.name,
            isDirectory: true,
            files: await listFilesRecursive(fullPath),
          }
        } else {
          return {
            name: entry.name,
            isDirectory: false,
          }
        }
      })
    )
  } catch (error) {
    console.error(`Failed to read directory ${dirPath}:`, error)
    return []
  }
}

// List all generated workflows and their files
app.get('/agent-factory/workflows', async (_req: Request, res: Response) => {
  const workflowsDir = path.resolve(__dirname, '../../generated_workflows')

  try {
    const entries = await fs.readdir(workflowsDir, { withFileTypes: true })
    const result = await Promise.all(
      entries
        .filter((entry) => entry.isDirectory())
        .map(async (entry) => ({
          name: entry.name,
          isDirectory: true,
          files: await listFilesRecursive(path.join(workflowsDir, entry.name)),
        }))
    )

    res.json(result)
  } catch (error) {
    console.error('Failed to read workflows directory:', error)
    res.status(500).json({ error: 'Failed to read workflows directory' })
  }
})

// Define workflows directory path
const workflowsDir = path.resolve(__dirname, '../../generated_workflows')

// Serve static files from workflows directory
app.use('/agent-factory/workflows', express.static(workflowsDir, {
  setHeaders: (res, filepath) => {
    // Set content type for code and text files
    if (filepath.match(/\.(py|md|txt|json|js|ts|yaml|yml)$/i)) {
      res.setHeader('Content-Type', 'text/plain; charset=utf-8')
    }
  }
}))

// Global error handler
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error('Unhandled error:', err)
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'production' ? undefined : err.message
  })
})

// Start the server
const server: Server = app.listen(PORT, () => {
  console.log(`✅ Server is running on http://localhost:${PORT}`)
})

// Handle server errors
server.on('error', (err: NodeJS.ErrnoException) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Port ${PORT} is already in use!`)
  } else {
    console.error('❌ Server error:', err)
  }
  process.exit(1)
})

// Handle graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully')
  server.close(() => {
    console.log('Server closed')
    process.exit(0)
  })
})
