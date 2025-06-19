import { Request, Response } from 'express'
import path from 'node:path'
import fs from 'node:fs/promises'
import { runPythonScriptWithStreaming } from '../helpers/agent-factory-helpers.js'
import { setupStreamingResponse } from '../utils/stream.utils.js'
import { resolveWorkflowPath } from '../utils/path.utils.js'
import {
  saveEvaluationCriteria as saveCriteria,
  EvaluationCriteria,
} from '../services/evaluation.service.js'

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
      'eval/generate_evaluation_case.py',
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
    // let outputText = ''
    const outputCallback = (source: 'stdout' | 'stderr', text: string) => {
      if (source === 'stdout') {
        console.log(`[evaluation stdout]: ${text}`)
        // outputText += text
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
      ['eval.run_generated_agent_evaluation'] as string[],
      outputCallback,
      env,
    )

    // Parse the evaluation results from output
    // const evaluationResults = parseEvaluationOutput(outputText)

    // // Save the results to a JSON file
    // const resultsPath = path.join(fullPath, 'evaluation_results.json')
    // await fs.writeFile(
    //   resultsPath,
    //   JSON.stringify(evaluationResults, null, 2),
    //   'utf8',
    // )

    // console.log(`Evaluation results saved to ${resultsPath}`)

    res.end(
      '\n[Agent evaluation completed. Results saved to evaluation_results.json]',
    )
  } catch (error: unknown) {
    console.error('Error running agent evaluation:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).send(`[Error running agent evaluation]: ${errorMessage}`)
  }
}

// Save custom evaluation criteria
export async function saveEvaluationCriteria(
  req: Request,
  res: Response,
): Promise<void> {
  try {
    const workflowPath = req.params.workflowPath
    const criteriaData = req.body as EvaluationCriteria

    if (!criteriaData.llm_judge || !Array.isArray(criteriaData.checkpoints)) {
      res.status(400).json({
        error:
          'Invalid evaluation criteria format, llm_judge is missing or checkpoints is not an array',
      })
      return
    }

    // Ensure all checkpoints have required fields
    for (const checkpoint of criteriaData.checkpoints) {
      if (!checkpoint.criteria || typeof checkpoint.points !== 'number') {
        res.status(400).json({
          error:
            'Invalid checkpoint format, a checkpoint doesnt have criteria or points is not a number',
        })
        return
      }
    }

    const result = await saveCriteria(workflowPath, criteriaData)
    // delete evaluation-results.json if it exists
    const resultsPath = path.join(
      resolveWorkflowPath(workflowPath),
      'evaluation_results.json',
    )
    try {
      await fs.unlink(resultsPath)
    } catch (error) {
      console.warn(`Could not delete existing evaluation results: ${error}`)
    }

    res.json({
      success: true,
      message: 'Evaluation criteria saved successfully',
      path: result.path,
    })
  } catch (error: unknown) {
    console.error('Error saving evaluation criteria:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res
      .status(500)
      .json({ error: `Failed to save evaluation criteria: ${errorMessage}` })
  }
}

// Delete agent evaluation trace file
export async function deleteAgentEvalTrace(
  req: Request,
  res: Response,
): Promise<void> {
  try {
    const workflowPath = req.params.workflowPath
    const fullPath = resolveWorkflowPath(workflowPath)
    const filePath = path.join(fullPath, 'agent_eval_trace.json')

    try {
      await fs.access(filePath)
    } catch {
      res.status(404).json({
        success: false,
        message: 'Agent evaluation trace file not found',
      })
      return
    }

    await fs.unlink(filePath)

    // Also delete results if they exist
    const resultsPath = path.join(fullPath, 'evaluation_results.json')
    try {
      await fs.access(resultsPath)
      await fs.unlink(resultsPath)
    } catch {
      // If results don't exist, ignore
    }

    res.status(200).json({
      success: true,
      message: 'Agent evaluation trace deleted successfully',
    })
  } catch (error: unknown) {
    console.error('Error deleting agent evaluation trace:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).json({
      success: false,
      message: `Failed to delete file: ${errorMessage}`,
    })
  }
}

// Delete evaluation criteria file
export async function deleteEvaluationCriteria(
  req: Request,
  res: Response,
): Promise<void> {
  try {
    const workflowPath = req.params.workflowPath
    const fullPath = resolveWorkflowPath(workflowPath)
    const criteriaPath = path.join(fullPath, 'evaluation_case.yaml')

    try {
      await fs.access(criteriaPath)
    } catch {
      res
        .status(404)
        .json({ success: false, message: 'Evaluation criteria file not found' })
      return
    }

    await fs.unlink(criteriaPath)

    // Also delete results if they exist
    const resultsPath = path.join(fullPath, 'evaluation_results.json')
    try {
      await fs.access(resultsPath)
      await fs.unlink(resultsPath)
    } catch {
      // If results don't exist, ignore
    }

    res.status(200).json({
      success: true,
      message: 'Evaluation criteria deleted successfully',
    })
  } catch (error: unknown) {
    console.error('Error deleting evaluation criteria:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).json({
      success: false,
      message: `Failed to delete file: ${errorMessage}`,
    })
  }
}

// Delete evaluation results file
export async function deleteEvaluationResults(
  req: Request,
  res: Response,
): Promise<void> {
  try {
    const workflowPath = req.params.workflowPath
    const fullPath = resolveWorkflowPath(workflowPath)
    const filePath = path.join(fullPath, 'evaluation_results.json')

    try {
      await fs.access(filePath)
    } catch {
      res
        .status(404)
        .json({ success: false, message: 'Evaluation results file not found' })
      return
    }

    await fs.unlink(filePath)

    res.status(200).json({
      success: true,
      message: 'Evaluation results deleted successfully',
    })
  } catch (error: unknown) {
    console.error('Error deleting evaluation results:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).json({
      success: false,
      message: `Failed to delete file: ${errorMessage}`,
    })
  }
}
