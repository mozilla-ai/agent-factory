import express from 'express'
import dotenv from 'dotenv'
import cors from 'cors'
import {
  runAgentFactoryWorkflowWithStreaming,
  getRunningPythonProcess,
  stopRunningPythonProcess,
} from './helpers/agent-factory-helpers.js'

dotenv.config()

const app = express()
const PORT = process.env.PORT || 3000

// Middleware
app.use(express.json())
app.use(cors())
app.use(express.urlencoded({ extended: true }))

// Set up routes
app.get('/', (req, res) => {
  res.send('Hello World!')
})

app.get('/agent-factory', (req, res) => {
  res.setHeader('Content-Type', 'text/plain; charset=utf-8') // <-- Add this line
  const prompt =
    (req.query.prompt as string) ||
    'Summarize text content from a given webpage URL'

  runAgentFactoryWorkflowWithStreaming(prompt, (source, text) => {
    if (source === 'stdout') {
      res.write(`[agent-factory stdout]: ${text}`)
    } else if (source === 'stderr') {
      res.write(`[agent-factory stderr]: ${text}`)
    }
  })
    .then(() => {
      res.end('\n[agent-factory] Workflow completed successfully.')
    })
    .catch((err) => {
      console.error('Error during agent factory workflow:', err)
      res.status(500).send(`[agent-factory] Workflow failed: ${err.message}`)
    })
})

// New endpoint to send input to the running Python process
app.post('/agent-factory/input', (req, res) => {
  const { input } = req.body
  const proc = getRunningPythonProcess()
  if (!proc) {
    return res.status(400).send('No running Python process')
  }
  proc.stdin.write(input + '\n')
  res.send('Input sent to Python process')
})

// Optional: Endpoint to stop the running Python process
app.post('/agent-factory/stop', (req, res) => {
  stopRunningPythonProcess()
  res.send('Python process stopped')
})

// Start the server
const server = app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`)
})

server.on('error', (err: any) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Port ${PORT} is already in use!`)
  } else {
    console.error('❌ Server error:', err)
  }
  process.exit(1)
})
