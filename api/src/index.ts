import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import { config } from './config/index.js'
import { processService } from './services/process.service.js'
import { errorHandler, notFoundHandler } from './middleware/error.middleware.js'
import { requestLogger, errorLogger } from './middleware/logging.middleware.js'
import agentRoutes from './routes/agent.routes.js'
import evaluationRoutes from './routes/evaluation.routes.js'
import workflowRoutes from './routes/workflow.routes.js'

// Load environment variables
dotenv.config()

const app = express()

// Basic middleware
app.use(cors())
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

// Request logging
app.use(requestLogger)

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    environment: config.environment,
    ready: processService.isEnvironmentReady(),
  })
})

// Static file serving for workflows
app.use(
  '/workflows',
  express.static(config.workflowsDir, {
    setHeaders: (res, filepath) => {
      // Set content type for code and text files
      if (filepath.match(/\.(py|md|txt|json|js|ts|yaml|yml)$/i)) {
        res.setHeader('Content-Type', 'text/plain; charset=utf-8')
      }
    },
  }),
)

// API routes
app.use('/api/agent', agentRoutes)
app.use('/api/evaluation', evaluationRoutes)
app.use('/api/workflows', workflowRoutes)

// Error handling
app.use(errorLogger)
app.use(notFoundHandler)
app.use(errorHandler)

// Initialize environment and start server
async function startServer() {
  try {
    await processService.initializeEnvironment()
    console.log('Environment initialized successfully')

    app.listen(config.port, () => {
      console.log(`Server running on port ${config.port}`)
      console.log(`Environment: ${config.environment}`)
      console.log(`Health check: http://localhost:${config.port}/health`)
    })
  } catch (error) {
    console.error('Failed to initialize environment:', error)
    process.exit(1)
  }
}

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\nReceived SIGINT, shutting down gracefully...')
  processService.stopAllProcesses()
  process.exit(0)
})

process.on('SIGTERM', () => {
  console.log('\nReceived SIGTERM, shutting down gracefully...')
  processService.stopAllProcesses()
  process.exit(0)
})

startServer()
