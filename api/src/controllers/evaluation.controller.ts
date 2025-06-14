import { Request, Response } from 'express'
import path from 'node:path'
import fs from 'node:fs/promises'
import { runPythonScriptWithStreaming } from '../helpers/agent-factory-helpers.js'
import { setupStreamingResponse } from '../utils/stream.utils.js'
import { resolveWorkflowPath } from '../utils/path.utils.js'
import { parseEvaluationOutput } from '../utils/evaluation.utils.js'

// 1. Run agent (generates agent_eval_trace.json)
export async function runAgent(req: Request, res: Response): Promise<void> {
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
      res.status(404).send(`Agent not found at path: ${workflowPath}/agent.py`)
      return
    }

    // Set the AGENT_WORKFLOW_DIR environment variable
    await runPythonScriptWithStreaming(
      agentPath,
      [], // No command line args needed
      outputCallback,
      {
        // Cast to NodeJS.ProcessEnv
        ...process.env,
        AGENT_WORKFLOW_DIR: `${process.cwd()}/generated_workflows/latest`,
      } as NodeJS.ProcessEnv,
    )

    // Check if we need to copy the trace file to a different workflow directory
    if (workflowPath !== 'latest') {
      const latestWorkflowDir = path.resolve(
        process.cwd(),
        'generated_workflows/latest',
      )
      const targetWorkflowDir = fullPath

      const sourceTracePath = path.join(
        latestWorkflowDir,
        'agent_eval_trace.json',
      )
      const targetTracePath = path.join(
        targetWorkflowDir,
        'agent_eval_trace.json',
      )

      try {
        await fs.access(sourceTracePath)
        await fs.copyFile(sourceTracePath, targetTracePath)
        console.log(
          `Copied agent trace from ${sourceTracePath} to ${targetTracePath}`,
        )
      } catch (copyError) {
        console.error('Error copying agent trace file:', copyError)
      }
    }

    res.end('\n[Agent run completed. Generated agent_eval_trace.json]')
  } catch (error: unknown) {
    console.error('Error running agent:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).send(`[Error running agent]: ${errorMessage}`)
  }
}

// 2. Generate evaluation cases
export async function generateEvaluationCases(
  req: Request,
  res: Response,
): Promise<void> {
  try {
    const workflowPath = req.params.workflowPath
    const fullPath = resolveWorkflowPath(workflowPath)

    const workflowName = workflowPath.startsWith('archive/')
      ? workflowPath
      : 'latest'

    console.log({
      workflowPath,
      fullPath,
      workflowName,
    })

    const outputCallback = setupStreamingResponse(res)

    await runPythonScriptWithStreaming(
      'eval/main.py',
      [`generated_workflows/${workflowName}`] as string[],
      outputCallback,
    )

    res.end(
      '\n[Evaluation cases generation completed. Saved to evaluation_case.yaml]',
    )
  } catch (error: unknown) {
    console.error('Error generating evaluation cases:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).send(`[Error generating evaluation cases]: ${errorMessage}`)
  }
}

// 3. Run agent evaluation
export async function runEvaluation(
  req: Request,
  res: Response,
): Promise<void> {
  try {
    const workflowPath = req.params.workflowPath
    const fullPath = resolveWorkflowPath(workflowPath)

    // Check if agent trace exists in the workflow directory
    const tracePath = path.join(fullPath, 'agent_eval_trace.json')

    try {
      await fs.access(tracePath)
    } catch {
      res
        .status(404)
        .send('Agent trace file not found. Make sure to run the agent first.')
      return
    }

    // Check if evaluation cases exist
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
    let outputText = ''
    const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
      if (source === 'stdout') {
        console.log(`[evaluation stdout]: ${text}`)
        outputText += text
        res.write(`[stdout]: ${text}`)
      } else if (source === 'stderr') {
        console.log(`[evaluation stderr]: ${text}`)
        res.write(`[stderr]: ${text}`)
      }
    }

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
    const evaluationResults = parseEvaluationOutput(outputText)

    // Save the results to a JSON file
    const resultsPath = path.join(fullPath, 'evaluation_results.json')
    await fs.writeFile(
      resultsPath,
      JSON.stringify(evaluationResults, null, 2),
      'utf8',
    )

    console.log(`Evaluation results saved to ${resultsPath}`)

    res.end(
      '\n[Agent evaluation completed. Results saved to evaluation_results.json]',
    )
  } catch (error: unknown) {
    console.error('Error running agent evaluation:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).send(`[Error running agent evaluation]: ${errorMessage}`)
  }
}
