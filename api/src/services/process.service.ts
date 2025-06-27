import { spawn, ChildProcess } from 'child_process'
import { config } from '../config/index.js'
import type { OutputCallback } from '../types/index.js'
import { getWorkflowPath } from '../config/index.js'

interface ProcessInfo {
  process: ChildProcess
  workflowPath: string
}

export class ProcessService {
  private processes = new Map<string, ProcessInfo>()
  private isEnvironmentInitialized = false
  private agentFactoryProcess: ChildProcess | null = null

  private formatProcessOutput(data: Buffer, processId: string): string {
    const output = data.toString()
    const timestamp = new Date().toISOString()
    const logPrefix = `[${timestamp}] [${processId}]`
    return output
      .split('\n')
      .filter((line) => line.trim())
      .map((line) => `${logPrefix} ${line}`)
      .join('\n')
  }

  // Initialize Python environment
  async initializeEnvironment(): Promise<void> {
    if (this.isEnvironmentInitialized) {
      return
    }

    console.log('Initializing Python environment...')

    try {
      // Check if the configured Python executable is available
      await this.runCommand(
        config.pythonExecutable,
        ['--version'],
        'python-check',
      )
      console.log(`Python is available at: ${config.pythonExecutable}`)
    } catch {
      console.log(`Configured Python not found at: ${config.pythonExecutable}`)
      console.log('Trying fallback python3...')
      try {
        await this.runCommand('python3', ['--version'], 'python3-check')
        console.log('Python3 is available')
        // Update config to use python3
        config.pythonExecutable = 'python3'
      } catch {
        throw new Error(
          `Failed to initialize Python environment. Neither ${config.pythonExecutable} nor python3 are available.`,
        )
      }
    }

    // TODO: Potentially install Python dependencies here in the future
    // For now, we assume dependencies are already installed

    this.isEnvironmentInitialized = true
    console.log('Python environment initialized successfully')
  }

  // Run command
  private async runCommand(
    command: string,
    args: string[],
    processId: string,
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      let stdoutBuffer = ''
      let stderrBuffer = ''

      const process = spawn(command, args, { stdio: 'pipe' })

      process.stdout.on('data', (data) => {
        stdoutBuffer += data.toString()
      })

      process.stderr.on('data', (data) => {
        stderrBuffer += data.toString()
      })

      process.on('error', (error) => {
        console.error(`Error in ${processId}:`, error)
        reject(new Error(`Failed to run ${processId}`))
      })

      process.on('exit', (code) => {
        if (code === 0) {
          console.log(`✅ ${processId} completed successfully`)
          if (stdoutBuffer) {
            console.log(`stdout: ${stdoutBuffer.split('\n')[0]}...`)
          }
          resolve()
        } else {
          console.error(`❌ ${processId} failed with code ${code}`)
          console.error(`stdout: ${stdoutBuffer}`)
          console.error(`stderr: ${stderrBuffer}`)
          reject(new Error(`${processId} failed with code ${code}`))
        }
      })
    })
  }

  // Run Agent Factory workflow
  async runAgentFactory(
    prompt: string,
    outputCallback: OutputCallback,
  ): Promise<void> {
    const processId = 'agent-factory'

    if (this.processes.has(processId)) {
      throw new Error('Agent factory process is already running')
    }

    // Agent factory is just a Python executable, so use runPythonScript with custom process ID
    return this.runPythonScriptWithProcessId(
      config.agentFactoryExecutable,
      [prompt],
      outputCallback,
      processId,
      'Agent Factory',
      prompt, // workflowPath
    )
  }

  // Run Python script with streaming
  async runPythonScript(
    scriptPath: string,
    args: string[] = [],
    outputCallback: OutputCallback,
    env: NodeJS.ProcessEnv | null = null,
  ): Promise<void> {
    const processId = `python-${Date.now()}`

    return this.runPythonScriptWithProcessId(
      config.pythonExecutable,
      [scriptPath, ...args],
      outputCallback,
      processId,
      'Python',
      scriptPath,
      env,
    )
  }

  // Internal method to run any executable with custom process ID
  private async runPythonScriptWithProcessId(
    executable: string,
    args: string[],
    outputCallback: OutputCallback,
    processId: string,
    logPrefix: string,
    workflowPath: string,
    env: NodeJS.ProcessEnv | null = null,
  ): Promise<void> {
    console.log(`Running ${logPrefix}: ${executable} ${args.join(' ')}`)

    const childProcess = spawn(executable, args, {
      cwd: config.rootDir,
      env: env || process.env,
    })

    this.processes.set(processId, {
      process: childProcess,
      workflowPath,
    })

    return new Promise((resolve, reject) => {
      childProcess.stdout?.on('data', (data) => {
        const output = data.toString()
        console.log(`[${logPrefix}] ${output.trim()}`)
        outputCallback('stdout', output)
      })

      childProcess.stderr?.on('data', (data) => {
        const output = data.toString()
        console.error(`[${logPrefix} ERROR] ${output.trim()}`)
        outputCallback('stderr', output)
      })

      childProcess.on('error', (_error) => {
        this.processes.delete(processId)
        reject(new Error(`${logPrefix} process failed`))
      })

      childProcess.on('exit', (code) => {
        this.processes.delete(processId)
        if (code === 0) {
          console.log(`[${logPrefix}] Process completed: ${workflowPath}`)
          resolve()
        } else {
          console.error(`[${logPrefix}] Process failed with exit code ${code}`)
          reject(new Error(`${logPrefix} process failed with code ${code}`))
        }
      })
    })
  }

  // Send input to a specific process
  sendInput(processId: string, input: string): boolean {
    const processInfo = this.processes.get(processId)
    if (!processInfo) {
      return false
    }

    const process = processInfo.process
    if (!process || !process.stdin) {
      return false
    }

    try {
      process.stdin.write(`${input}\n`)
      return true
    } catch {
      console.error('Error sending input to process')
      return false
    }
  }

  // Get running process by ID
  getProcess(processId: string): ChildProcess | undefined {
    const processInfo = this.processes.get(processId)
    if (!processInfo) {
      return undefined
    }

    return processInfo.process
  }

  // Get process info
  getProcessInfo(processId: string): ProcessInfo | null {
    const processInfo = this.processes.get(processId)
    if (!processInfo) {
      return null
    }

    return {
      process: processInfo.process,
      workflowPath: processInfo.workflowPath,
    }
  }

  // Stop a specific process
  stopProcess(processId: string): boolean {
    const processInfo = this.processes.get(processId)
    if (!processInfo) {
      return false
    }

    const process = processInfo.process
    if (!process) {
      return false
    }

    try {
      process.kill()
      this.processes.delete(processId)
      return true
    } catch {
      console.error('Error stopping process')
      return false
    }
  }

  // Stop all processes
  stopAllProcesses(): void {
    for (const [processId, processInfo] of this.processes) {
      try {
        processInfo.process.kill()
        console.log(`Stopped process: ${processId}`)
      } catch {
        console.error(`Error stopping process ${processId}`)
      }
    }
    this.processes.clear()
  }

  // Check if environment is ready
  isEnvironmentReady(): boolean {
    return this.isEnvironmentInitialized
  }

  // Get currently running agent factory process
  getAgentFactoryProcess(): ProcessInfo | undefined {
    return this.processes.get('agent-factory')
  }

  // Run agent generation
  async runAgentGeneration(
    workflowPath: string,
    onOutput?: OutputCallback,
  ): Promise<void> {
    await this.initializeEnvironment()

    return new Promise((resolve, reject) => {
      const processId = 'agent-generation'
      const fullWorkflowPath = getWorkflowPath(workflowPath)

      const agentFactoryProcess = spawn(
        config.pythonExecutable,
        ['-m', 'agent_factory.generation', fullWorkflowPath],
        {
          stdio: 'pipe',
          cwd: config.rootDir,
        },
      )

      let hasErrored = false

      agentFactoryProcess.stdout?.on('data', (data) => {
        const formattedOutput = this.formatProcessOutput(data, processId)
        onOutput?.('stdout', formattedOutput)
      })

      agentFactoryProcess.stderr?.on('data', (data) => {
        const formattedOutput = this.formatProcessOutput(data, processId)
        onOutput?.('stderr', formattedOutput)
        hasErrored = true
      })

      agentFactoryProcess.on('close', (code) => {
        if (code === 0 && !hasErrored) {
          resolve()
        } else {
          reject(new Error(`${processId} failed with code ${code}`))
        }
      })

      agentFactoryProcess.on('error', (_err) => {
        reject(new Error(`Failed to run ${processId}`))
      })
    })
  }

  // Run agent evaluation
  async runAgentEvaluation(
    workflowPath: string,
    onOutput?: OutputCallback,
  ): Promise<void> {
    if (this.agentFactoryProcess) {
      throw new Error('Agent factory process is already running')
    }

    await this.initializeEnvironment()

    return new Promise((resolve, reject) => {
      const processId = 'agent-evaluation'
      const fullWorkflowPath = getWorkflowPath(workflowPath)

      // Build the specific file paths that the Python script expects
      const evaluationCaseFile = `${fullWorkflowPath}/evaluation_case.yaml`
      const agentTraceFile = `${fullWorkflowPath}/agent_eval_trace.json`
      const resultsFile = `${fullWorkflowPath}/evaluation_results.json`

      this.agentFactoryProcess = spawn(
        config.pythonExecutable,
        [
          '-m',
          'eval.run_generated_agent_evaluation',
          '--evaluation_case_json_file',
          evaluationCaseFile,
          '--agent_trace_json_file',
          agentTraceFile,
          '--save_evaluation_results_path',
          resultsFile,
        ],
        {
          stdio: 'pipe',
          cwd: config.rootDir,
        },
      )

      let hasErrored = false

      this.agentFactoryProcess.stdout?.on('data', (data) => {
        const formattedOutput = this.formatProcessOutput(data, processId)
        onOutput?.('stdout', formattedOutput)
      })

      this.agentFactoryProcess.stderr?.on('data', (data) => {
        const formattedOutput = this.formatProcessOutput(data, processId)
        onOutput?.('stderr', formattedOutput)
        hasErrored = true
      })

      this.agentFactoryProcess.on('close', (code) => {
        this.agentFactoryProcess = null
        if (code === 0 && !hasErrored) {
          resolve()
        } else {
          reject(new Error(`${processId} failed with code ${code}`))
        }
      })

      this.agentFactoryProcess.on('error', (_err) => {
        this.agentFactoryProcess = null
        reject(new Error(`${processId} process failed`))
      })
    })
  }

  // Stop the agent factory process
  stopAgentFactory(): void {
    if (this.agentFactoryProcess) {
      this.agentFactoryProcess.kill()
      this.agentFactoryProcess = null
    }
  }
}

// Singleton instance
export const processService = new ProcessService()
