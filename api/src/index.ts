import express, { Request, Response, NextFunction } from 'express'
import dotenv from 'dotenv'
import cors from 'cors'
import {
  runAgentFactoryWorkflowWithStreaming,
  getRunningPythonProcess,
  stopRunningPythonProcess,
  runPythonScriptWithStreaming,
  initializeEnvironment,
  isEnvironmentReady,
} from './helpers/agent-factory-helpers.js'
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Server } from 'node:http'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Load environment variables
dotenv.config()

export type FileEntry = {
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

// Resolve workflow path based on path param (latest or archive/<workflow_id>)
function resolveWorkflowPath(workflowPath: string): string {
  const workflowsDir = path.resolve(__dirname, '../../generated_workflows')

  if (workflowPath === 'latest') {
    return path.join(workflowsDir, 'latest')
  } else if (workflowPath.startsWith('archive/')) {
    return path.join(workflowsDir, workflowPath)
  } else {
    throw new Error(
      'Invalid workflow path. Must be "latest" or start with "archive/"',
    )
  }
}

// Common streaming handler setup for evaluation endpoints
function setupStreamingResponse(res: Response) {
  res.setHeader('Content-Type', 'text/plain; charset=utf-8')
  return (source: 'stdout' | 'stderr', text: string) => {
    if (source === 'stdout') {
      console.log(`[evaluation stdout]: ${text}`)
      res.write(`[stdout]: ${text}`)
    } else if (source === 'stderr') {
      console.log(`[evaluation stderr]: ${text}`)
      res.write(`[stderr]: ${text}`)
    }
  }
}

// 1. Run agent (generates agent_eval_trace.json) - UPDATED
app.post(
  '/agent-factory/evaluate/run-agent/:workflowPath',
  async (req: Request, res: Response): Promise<void> => {
    try {
      const workflowPath = req.params.workflowPath
      const fullPath = resolveWorkflowPath(workflowPath)

      // Use the same pattern as in generate-cases
      const workflowName = workflowPath.startsWith('archive/')
        ? workflowPath
        : 'latest'

      console.log({
        workflowPath,
        fullPath,
        workflowName,
      })

      const outputCallback = setupStreamingResponse(res)

      const agentPath = path.join(fullPath, 'agent.py')

      // Check if agent.py exists
      try {
        await fs.access(agentPath)
      } catch {
        res
          .status(404)
          .send(`Agent not found at path: ${workflowPath}/agent.py`)
        return
      }

      // Set the AGENT_WORKFLOW_DIR environment variable to tell the agent where to save the trace
      await runPythonScriptWithStreaming(
        agentPath,
        [], // No command line args needed with environment variables
        outputCallback,
        {
          // Cast to NodeJS.ProcessEnv
          ...process.env,
          AGENT_WORKFLOW_DIR: `${process.cwd()}/generated_workflows/${workflowName}`,
        } as NodeJS.ProcessEnv,
      )

      res.end('\n[Agent run completed. Generated agent_eval_trace.json]')
    } catch (error: unknown) {
      console.error('Error running agent:', error)
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      res.status(500).send(`[Error running agent]: ${errorMessage}`)
    }
  },
)

// 2. Generate evaluation cases - with workflowPath parameter
app.post(
  '/agent-factory/evaluate/generate-cases/:workflowPath',
  async (req: Request, res: Response): Promise<void> => {
    try {
      const workflowPath = req.params.workflowPath
      const fullPath = resolveWorkflowPath(workflowPath)

      // ⚠️ FIX: Make sure we're only passing the workflow-relative path, not the full system path
      // Instead of this:
      // const relativePath = fullPath.replace(process.cwd(), '').replace(/^\//, '');

      // Do this - just pass the workflow name directly:
      const workflowName = workflowPath.startsWith('archive/')
        ? workflowPath
        : 'latest'

      console.log({
        workflowPath,
        fullPath,
        workflowName, // Use this simpler path
      })

      const outputCallback = setupStreamingResponse(res)

      // Pass just the workflow name to the Python script
      await runPythonScriptWithStreaming(
        'eval/main.py',
        [`generated_workflows/${workflowName}`] as string[], // Fix using type assertion
        outputCallback,
      )

      res.end(
        '\n[Evaluation cases generation completed. Saved to evaluation_case.yaml]',
      )
    } catch (error: unknown) {
      console.error('Error generating evaluation cases:', error)
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      res
        .status(500)
        .send(`[Error generating evaluation cases]: ${errorMessage}`)
    }
  },
)

// 3. Run agent evaluation (original version)
app.post(
  '/agent-factory/evaluate/run-evaluation/:workflowPath',
  async (req: Request, res: Response): Promise<void> => {
    try {
      const workflowPath = req.params.workflowPath
      const fullPath = resolveWorkflowPath(workflowPath)

      // Check if agent trace exists in the workflow directory
      const tracePath = path.join(fullPath, 'agent_eval_trace.json')

      // Fix both return statements
      try {
        await fs.access(tracePath)
      } catch {
        res
          .status(404)
          .send('Agent trace file not found. Make sure to run the agent first.')
        return
      }

      // Check if evaluation cases exist (globally)
      try {
        await fs.access(path.resolve(fullPath, 'evaluation_case.yaml'))
      } catch {
        res
          .status(404)
          .send(
            'Evaluation cases not found. Make sure to generate evaluation cases first.',
          )
        return
      }

      // Collect all stdout for parsing
      let outputText = '';
      const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
        if (source === 'stdout') {
          console.log(`[evaluation stdout]: ${text}`);
          outputText += text;
          res.write(`[stdout]: ${text}`);
        } else if (source === 'stderr') {
          console.log(`[evaluation stderr]: ${text}`);
          res.write(`[stderr]: ${text}`);
        }
      };

      // Set environment variables for the evaluation script
      const env = {
        ...process.env,
        AGENT_PATH: fullPath,
      }

      await runPythonScriptWithStreaming(
        '-m',
        ['eval.run_agent_eval'] as string[],
        outputCallback,
        env,
      )

      // Parse the evaluation results from output
      const evaluationResults = parseEvaluationOutput(outputText);

      // Save the results to a JSON file
      const resultsPath = path.join(fullPath, 'evaluation_results.json');
      await fs.writeFile(
        resultsPath,
        JSON.stringify(evaluationResults, null, 2),
        'utf8'
      );

      console.log(`Evaluation results saved to ${resultsPath}`);

      res.end(
        '\n[Agent evaluation completed. Results saved to evaluation_results.json]',
      )
    } catch (error: unknown) {
      console.error('Error running agent evaluation:', error)
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      res.status(500).send(`[Error running agent evaluation]: ${errorMessage}`)
    }
  },
)

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
      }),
    )
  } catch (error) {
    console.error(`Failed to read directory ${dirPath}:`, error)
    return []
  }
}

// List all generated workflows and their files
app.get(
  '/agent-factory/workflows',
  async (_req: Request, res: Response): Promise<void> => {
    const workflowsDir = path.resolve(__dirname, '../../generated_workflows')

    try {
      // Check if directory exists first
      try {
        await fs.access(workflowsDir)
      } catch {
        // Directory doesn't exist, return empty array
        console.log('Workflows directory does not exist, returning empty array')
        res.json([])
        return
      }

      // Directory exists, read its contents
      const entries = await fs.readdir(workflowsDir, { withFileTypes: true })

      // If no entries or no directories, return empty array
      if (
        entries.length === 0 ||
        !entries.some((entry) => entry.isDirectory())
      ) {
        res.json([])
        return
      }

      const result = await Promise.all(
        entries
          .filter((entry) => entry.isDirectory())
          .map(async (entry) => ({
            name: entry.name,
            isDirectory: true,
            files: await listFilesRecursive(
              path.join(workflowsDir, entry.name),
            ),
          })),
      )

      res.json(result)
    } catch (error) {
      // Only unexpected errors should return 500
      console.error('Unexpected error reading workflows directory:', error)
      res.status(500).json({ error: 'Failed to read workflows directory' })
    }
  },
)

// Define workflows directory path
const workflowsDir = path.resolve(__dirname, '../../generated_workflows')

// Serve static files from workflows directory
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

app.get('/', (_req: Request, res: Response) => {
  res.send('Hello World!')
})

// Run agent factory workflow
app.get('/agent-factory', async (req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/plain; charset=utf-8')
  const prompt =
    (req.query.prompt as string) ||
    'Summarize text content from a given webpage URL'

  try {
    await runAgentFactoryWorkflowWithStreaming(
      prompt,
      (source: 'stdout' | 'stderr', text: string) => {
        if (source === 'stdout') {
          console.log(`[agent-factory stdout]: ${text}`)
          res.write(`[agent-factory stdout]: ${text}`)
        } else if (source === 'stderr') {
          console.log(`[agent-factory stderr]: ${text}`)
          res.write(`[agent-factory stderr]: ${text}`)
        }
      },
    )
    res.end('\n[agent-factory] Workflow completed successfully.')
  } catch (error: unknown) {
    console.error('Error during agent factory workflow:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).send(`[agent-factory] Workflow failed: ${errorMessage}`)
  }
})

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

// Update middleware application
// Change this:
// app.use('/agent-factory', checkEnvironmentMiddleware)

// To this:
app.use('/agent-factory', (req: Request, res: Response, next: NextFunction) => {
  checkEnvironmentMiddleware(req, res, next)
})

// Start the server
startServer().catch((error) => {
  console.error('Failed to start server:', error)
  process.exit(1)
})

// Add these interfaces for evaluation results
interface EvaluationCheckpointResult {
  criteria: string;
  points: number;
  result: 'pass' | 'fail';
  feedback: string;
}

interface EvaluationResults {
  score: number;
  maxScore: number;
  checkpoints: EvaluationCheckpointResult[];
}

// Add this function to parse evaluation output
function parseEvaluationOutput(output: string): EvaluationResults {
  const results: EvaluationResults = {
    score: 0,
    maxScore: 0,
    checkpoints: []
  };

  // Extract final score
  const scoreMatch = output.match(/Final score: (\d+(?:\.\d+)?)/);
  if (scoreMatch) {
    results.score = parseFloat(scoreMatch[1]);
  }

  // Find the checkpoint results section
  const checkpointSections = output.split(/\s*Checkpoint \d+:/g);
  // Skip the first section which is the header
  if (checkpointSections.length > 1) {
    for (let i = 1; i < checkpointSections.length; i++) {
      const section = checkpointSections[i];

      // Extract the parts
      const criteriaMatch = section.match(/Criteria: (.*?)(?=\s*Criteria Points:)/s);
      const pointsMatch = section.match(/Criteria Points: (\d+)/);
      const passedMatch = section.match(/Passed: (True|False)/);
      const reasonMatch = section.match(/Reason: (.*?)(?=\s*(?:Checkpoint \d+:|$))/s);

      if (criteriaMatch && pointsMatch && passedMatch && reasonMatch) {
        const criteria = criteriaMatch[1].trim();
        const points = parseInt(pointsMatch[1], 10);
        const passed = passedMatch[1] === 'True';
        const reason = reasonMatch[1].trim();

        results.maxScore += points;

        results.checkpoints.push({
          criteria,
          points,
          result: passed ? 'pass' : 'fail',
          feedback: reason
        });
      }
    }
  }

  return results;
}
