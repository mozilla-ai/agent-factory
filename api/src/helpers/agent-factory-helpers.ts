import path from 'node:path'
import { spawn, ChildProcessWithoutNullStreams } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename) // get current directory of this file

const agentFactoryPath = path.resolve(__dirname, '../../../')
const venvPython = path.resolve(agentFactoryPath, '.venv/bin/python')
const venvUv = path.resolve(agentFactoryPath, '.venv/bin/uv')

let agentFactoryProcess: ChildProcessWithoutNullStreams | undefined

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
  const steps = [
    { name: 'ensurepip', fn: installPip },
    { name: 'install uv', fn: installUv },
    { name: 'uv sync', fn: runUvSync },
    { name: 'run python', fn: () => runAgentFactory(prompt) },
  ]

  for (const step of steps) {
    await new Promise<void>((resolve, reject) => {
      const cmd = step.fn()
      cmd.stdout.on('data', (data) => onData('stdout', data.toString()))
      cmd.stderr.on('data', (data) => onData('stderr', data.toString()))
      cmd.on('error', reject)
      cmd.on('exit', (code) => {
        if (code === 0) resolve()
        else reject(new Error(`${step.name} failed with code ${code}`))
      })
    })
  }
}
