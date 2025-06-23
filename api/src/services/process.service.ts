import { spawn, ChildProcess } from 'child_process'
import { config } from '../config/index.js'
import { ProcessError } from '../middleware/error.middleware.js'
import type { OutputCallback } from '../types/index.js'
import { PROCESS_IDS } from '../constants/index.js'

interface ProcessInfo {
  process: ChildProcess
  workflowPath: string
}

export class ProcessService {
  private processes = new Map<string, ProcessInfo>()
  private isEnvironmentInitialized = false

  // Initialize Python environment
  async initializeEnvironment(): Promise<void> {
    if (this.isEnvironmentInitialized) {
      return
    }

    console.log('Initializing Python environment...')

    try {
      // Just run uv sync - it will handle everything including installing itself if needed
      await this.runCommand(
        'uv',
        ['sync', '--project', config.rootDir],
        'uv-sync',
      )

      this.isEnvironmentInitialized = true
      console.log('Python environment initialized successfully')
    } catch (error) {
      // If uv is not installed globally, try to install it first
      console.log('uv not found, attempting to install...')

      try {
        // Install uv using pip (most reliable cross-platform method)
        await this.runCommand(
          config.pythonExecutable,
          ['-m', 'pip', 'install', 'uv'],
          'install-uv',
        )

        // Now run uv sync
        await this.runCommand(
          config.uvExecutable,
          ['sync', '--project', config.rootDir],
          'uv-sync',
        )

        this.isEnvironmentInitialized = true
        console.log('Python environment initialized successfully')
      } catch (installError) {
        throw new ProcessError('Failed to initialize Python environment', {
          originalError: error,
          installError,
        })
      }
    }
  }

  // Run a command and wait for completion
  private async runCommand(
    command: string,
    args: string[],
    processId: string,
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const process = spawn(command, args, {
        cwd: config.rootDir,
        shell: false,
      })

      let stdoutBuffer = ''
      let stderrBuffer = ''

      process.stdout.on('data', (data) => {
        stdoutBuffer += data.toString()
      })

      process.stderr.on('data', (data) => {
        stderrBuffer += data.toString()
      })

      process.on('error', (error) => {
        console.error(`Error in ${processId}:`, error)
        reject(
          new ProcessError(`Failed to run ${processId}`, {
            command,
            args,
            error: error.message,
          }),
        )
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
          reject(
            new ProcessError(`${processId} failed with code ${code}`, {
              command,
              args,
              exitCode: code,
              stdout: stdoutBuffer,
              stderr: stderrBuffer,
            }),
          )
        }
      })
    })
  }

  // Run Agent Factory workflow
  async runAgentFactory(
    prompt: string,
    outputCallback: OutputCallback,
  ): Promise<void> {
    const processId = PROCESS_IDS.AGENT_FACTORY

    if (this.processes.has(processId)) {
      throw new ProcessError('Agent factory process is already running')
    }

    const process = spawn(config.agentFactoryExecutable, [prompt], {
      cwd: config.rootDir,
      shell: false,
    })

    this.processes.set(processId, {
      process,
      workflowPath: prompt,
    })

    return new Promise((resolve, reject) => {
      process.stdout.on('data', (data) => {
        const output = data.toString()
        console.log(`[Agent Factory] ${output.trim()}`)
        outputCallback('stdout', output)
      })

      process.stderr.on('data', (data) => {
        const output = data.toString()
        console.error(`[Agent Factory ERROR] ${output.trim()}`)
        outputCallback('stderr', output)
      })

      process.on('error', (error) => {
        this.processes.delete(processId)
        reject(
          new ProcessError('Agent factory process failed', {
            error: error.message,
          }),
        )
      })

      process.on('exit', (code) => {
        this.processes.delete(processId)
        if (code === 0) {
          console.log('[Agent Factory] Process completed successfully')
          resolve()
        } else {
          console.error(`[Agent Factory] Process failed with exit code ${code}`)
          reject(
            new ProcessError(`Agent factory process failed with code ${code}`, {
              exitCode: code,
            }),
          )
        }
      })
    })
  }

  // Run Python script with streaming
  async runPythonScript(
    scriptPath: string,
    args: string[] = [],
    outputCallback: OutputCallback,
    env: NodeJS.ProcessEnv | null = null,
  ): Promise<void> {
    const processId = `python-${Date.now()}`

    console.log(
      `Running Python script: ${config.pythonExecutable} ${scriptPath} ${args.join(' ')}`,
    )

    const pythonProcess = spawn(
      config.pythonExecutable,
      [scriptPath, ...args],
      {
        cwd: config.rootDir,
        env: env || process.env,
      },
    )

    this.processes.set(processId, {
      process: pythonProcess,
      workflowPath: scriptPath,
    })

    return new Promise((resolve, reject) => {
      pythonProcess.stdout.on('data', (data: Buffer) => {
        const output = data.toString('utf-8')
        console.log(`[Python] ${output.trim()}`)
        outputCallback('stdout', output)
      })

      pythonProcess.stderr.on('data', (data: Buffer) => {
        const output = data.toString('utf-8')
        console.error(`[Python ERROR] ${output.trim()}`)
        outputCallback('stderr', output)
      })

      pythonProcess.on('error', (error: Error) => {
        this.processes.delete(processId)
        console.error(`[Python] Process error: ${error.message}`)
        reject(
          new ProcessError('Python script failed', {
            scriptPath,
            args,
            error: error.message,
          }),
        )
      })

      pythonProcess.on('close', (code: number | null) => {
        this.processes.delete(processId)
        if (code === 0) {
          console.log(`[Python] Script completed: ${scriptPath}`)
          resolve()
        } else {
          console.error(
            `[Python] Script failed with code ${code}: ${scriptPath}`,
          )
          reject(
            new ProcessError(`Python script failed with code ${code}`, {
              scriptPath,
              args,
              exitCode: code,
            }),
          )
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
    } catch (error) {
      console.error('Error sending input to process:', error)
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
    } catch (error) {
      console.error('Error stopping process:', error)
      return false
    }
  }

  // Stop all processes
  stopAllProcesses(): void {
    for (const [processId, processInfo] of this.processes) {
      try {
        processInfo.process.kill()
        console.log(`Stopped process: ${processId}`)
      } catch (error) {
        console.error(`Error stopping process ${processId}:`, error)
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
    return this.processes.get(PROCESS_IDS.AGENT_FACTORY)
  }
}

// Singleton instance
export const processService = new ProcessService()
