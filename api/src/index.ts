import express, { Request, Response, NextFunction } from 'express'
import dotenv from 'dotenv'
import cors from 'cors'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Server } from 'node:http'
import {
  initializeEnvironment,
  isEnvironmentReady,
  stopRunningPythonProcess,
} from './helpers/agent-factory-helpers.js'

// Import controllers
import { generateAgent } from './controllers/agent.controller.js'
import {
  runAgent,
  generateEvaluationCases,
  runEvaluation,
} from './controllers/evaluation.controller.js'
import { listWorkflows } from './controllers/workflow.controller.js'
import { sendInput, stopPythonProcess } from './controllers/input.controller.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Load environment variables
dotenv.config()

// Create Express application
const app = express()
const PORT = process.env.PORT || 3000

// Middleware setup
app.use(express.json())
app.use(cors())
app.use(express.urlencoded({ extended: true }))

// Define routes
app.get('/', (_req: Request, res: Response) => {
  res.send('Hello World!')
})

// Run agent factory workflow
app.get('/agent-factory', generateAgent)

// Evaluation endpoints
app.post('/agent-factory/evaluate/run-agent/:workflowPath', runAgent)
app.post(
  '/agent-factory/evaluate/generate-cases/:workflowPath',
  generateEvaluationCases,
)
app.post('/agent-factory/evaluate/run-evaluation/:workflowPath', runEvaluation)

// Input and process control
app.post('/agent-factory/input', sendInput)
app.post('/agent-factory/stop', stopPythonProcess)

// Workflow listing
app.get('/agent-factory/workflows', listWorkflows)

// Define workflows directory path
const workflowsDir = path.resolve(__dirname, '../../generated_workflows')

// Serve static files from workflows directory - KEPT EXACTLY AS IS
app.use(
  '/agent-factory/workflows',
  express.static(workflowsDir, {
    setHeaders: (res, filepath) => {
      // Set content type for code and text files
      if (filepath.match(/\.(py|md|txt|json|js|ts|yaml|yml)$/i)) {
        res.setHeader('Content-Type', 'text/plain; charset=utf-8')
      }
    },
  }),
)

// Global error handler
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error('Unhandled error:', err)
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'production' ? undefined : err.message,
  })
})

// Initialize the server
async function startServer() {
  try {
    // Initialize Python environment before starting server
    await initializeEnvironment()

    // Start listening once environment is ready
    const server = app.listen(PORT, () => {
      console.log(`Server is running on port ${PORT}`)
    })

    // Handle graceful shutdown
    setupGracefulShutdown(server)

    return server
  } catch (error) {
    console.error('Failed to initialize environment:', error)
    process.exit(1)
  }
}

// Handle server shutdown
function setupGracefulShutdown(server: Server) {
  // Handle graceful shutdown
  process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully')

    server.close(() => {
      console.log('Server closed, shutting down Python processes')

      // Then stop any running Python processes
      stopRunningPythonProcess()
      console.log('Python processes terminated')

      console.log('Shutdown complete')
      process.exit(0)
    })
  })

  // Also handle SIGINT (Ctrl+C) with similar cleanup
  process.on('SIGINT', () => {
    console.log('SIGINT received, shutting down gracefully')

    server.close(() => {
      console.log('Server closed, shutting down Python processes')

      // Then stop any running Python processes
      stopRunningPythonProcess()
      console.log('Python processes terminated')

      console.log('Shutdown complete')
      process.exit(0)
    })
  })
}

// Add middleware to check if environment is ready
const checkEnvironmentMiddleware = (
  req: Request,
  res: Response,
  next: NextFunction,
) => {
  if (!isEnvironmentReady()) {
    return res.status(503).json({
      error: 'Server is still initializing. Please try again in a few moments.',
    })
  }
  next()
}

app.use('/agent-factory', (req: Request, res: Response, next: NextFunction) => {
  checkEnvironmentMiddleware(req, res, next)
})

// Start the server
startServer().catch((error) => {
  console.error('Failed to start server:', error)
  process.exit(1)
})
