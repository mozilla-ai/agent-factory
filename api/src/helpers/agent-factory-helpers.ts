import path from 'node:path'
import { spawn, ChildProcessWithoutNullStreams } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename) // get current directory of this file

const agentFactoryPath = path.resolve(__dirname, '../../../')
const venvPython = path.resolve(agentFactoryPath, '.venv/bin/python')
const venvUv = path.resolve(agentFactoryPath, '.venv/bin/uv')

let agentFactoryProcess: ChildProcessWithoutNullStreams | undefined

// Flag to track initialization status
let isEnvironmentInitialized = false

// installs pip
export function installPip(): ChildProcessWithoutNullStreams {
  return spawn(venvPython, ['-m', 'ensurepip'], {
    cwd: agentFactoryPath,
    shell: false,
  })
}

// installs uv
export function installUv(): ChildProcessWithoutNullStreams {
  return spawn(venvPython, ['-m', 'pip', 'install', 'uv'], {
    cwd: agentFactoryPath,
    shell: false,
  })
}

// installs agent factory project dependencies
export function runUvSync(): ChildProcessWithoutNullStreams {
  return spawn(venvUv, ['sync', '--project', agentFactoryPath], {
    cwd: agentFactoryPath,
    shell: false,
  })
}

// Function to initialize the environment once
export async function initializeEnvironment(): Promise<void> {
  if (isEnvironmentInitialized) {
    console.log('Environment already initialized, skipping setup')
    return
  }

  console.log('Initializing Python environment...')

  const steps = [
    { name: 'ensurepip', fn: installPip },
    { name: 'install uv', fn: installUv },
    { name: 'uv sync', fn: runUvSync },
  ]

  for (const step of steps) {
    console.log(`Running initialization step: ${step.name}`)
    await new Promise<void>((resolve, reject) => {
      const cmd = step.fn()

      // Buffer stdout for logging
      let stdoutBuffer = ''
      let stderrBuffer = ''

      cmd.stdout.on('data', (data) => {
        const text = data.toString()
        stdoutBuffer += text
      })

      cmd.stderr.on('data', (data) => {
        const text = data.toString()
        stderrBuffer += text
      })

      cmd.on('error', (error) => {
        console.error(`Error in ${step.name}:`, error)
        reject(error)
      })

      cmd.on('exit', (code) => {
        if (code === 0) {
          console.log(`✅ ${step.name} completed successfully`)
          // Log brief output summary
          if (stdoutBuffer) {
            console.log(`stdout: ${stdoutBuffer.split('\n')[0]}...`)
          }
          resolve()
        } else {
          console.error(`❌ ${step.name} failed with code ${code}`)
          console.error(`stdout: ${stdoutBuffer}`)
          console.error(`stderr: ${stderrBuffer}`)
          reject(new Error(`${step.name} failed with code ${code}`))
        }
      })
    })
  }

  isEnvironmentInitialized = true
  console.log('✅ Python environment initialized successfully')
}

// runs the agent factory Python script
export function runAgentFactory(
  prompt = 'Summarize text content from a given webpage URL',
): ChildProcessWithoutNullStreams {
  // Store the process for later input
  agentFactoryProcess = spawn(venvPython, ['-m', 'src.main', prompt], {
    cwd: agentFactoryPath,
    shell: false,
  })
  return agentFactoryProcess
}

export function getRunningPythonProcess():
  | ChildProcessWithoutNullStreams
  | undefined {
  return agentFactoryProcess
}

export function stopRunningPythonProcess() {
  if (agentFactoryProcess) {
    agentFactoryProcess.kill()
    agentFactoryProcess = undefined
  }
}

// Example workflow using async/await and streaming output
export async function runAgentFactoryWorkflowWithStreaming(
  prompt: string = 'Summarize text content from a given webpage URL',
  onData: (source: 'stdout' | 'stderr', text: string) => void,
) {
  // Ensure environment is initialized
  try {
    // Just run the agent directly since setup is already handled
    const agentProcess = runAgentFactory(prompt)

    await new Promise<void>((resolve, reject) => {
      agentProcess.stdout.on('data', (data) => onData('stdout', data.toString()))
      agentProcess.stderr.on('data', (data) => onData('stderr', data.toString()))
      agentProcess.on('error', reject)
      agentProcess.on('exit', (code) => {
        if (code === 0) resolve()
        else reject(new Error(`Agent process failed with code ${code}`))
      })
    })
  } catch (error) {
    console.error('Error in agent factory workflow:', error)
    throw error
  }
}

// Add a new function to run any Python script with streaming output
export async function runPythonScriptWithStreaming(
  scriptPath,
  args = [],
  outputCallback,
  customEnv = null
) {
  return new Promise((resolve, reject) => {
    // Use the virtual environment Python when possible
    const pythonExecutable = venvPython

    console.log(`Running Python script: ${pythonExecutable} ${scriptPath} ${args.join(' ')}`)

    const pythonProcess = spawn(pythonExecutable, [scriptPath, ...args], {
      cwd: agentFactoryPath,
      env: customEnv || process.env,
    })

    // Handle stdout data
    pythonProcess.stdout.on('data', (data) => {
      const text = data.toString('utf-8')
      outputCallback('stdout', text)
    })

    // Handle stderr data
    pythonProcess.stderr.on('data', (data) => {
      const text = data.toString('utf-8')
      outputCallback('stderr', text)
    })

    // Handle process errors
    pythonProcess.on('error', (error) => {
      console.error(`Error running Python script:`, error)
      reject(error)
    })

    // Handle process completion
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        resolve()
      } else {
        reject(new Error(`Python process exited with code ${code}`))
      }
    })
  })
}

// Export the isEnvironmentInitialized flag for checking from outside
export function isEnvironmentReady(): boolean {
  return isEnvironmentInitialized
}
