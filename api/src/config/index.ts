import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { ApiConfig } from '../types/index.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Get the root directory of the project (agent-factory)
const rootDir = path.resolve(__dirname, '../../../')

// Build paths relative to root
const workflowsDir = path.resolve(rootDir, 'generated_workflows')
const venvDir = path.resolve(rootDir, '.venv')

// Platform-specific executable paths
const isWindows = process.platform === 'win32'
const pythonExecutable = path.join(
  venvDir,
  isWindows ? 'Scripts/python.exe' : 'bin/python',
)
const uvExecutable = path.join(venvDir, isWindows ? 'Scripts/uv.exe' : 'bin/uv')
const agentFactoryExecutable = path.join(
  venvDir,
  isWindows ? 'Scripts/agent-factory.exe' : 'bin/agent-factory',
)

export const config: ApiConfig = {
  port: parseInt(process.env.PORT || '3000', 10),
  workflowsDir,
  pythonExecutable,
  uvExecutable,
  agentFactoryExecutable,
  environment:
    (process.env.NODE_ENV as ApiConfig['environment']) || 'development',
  rootDir,
}

// Helper functions
export function getWorkflowPath(workflowPath: string = ''): string {
  return path.join(config.workflowsDir, workflowPath)
}

export function isProduction(): boolean {
  return config.environment === 'production'
}

export function isDevelopment(): boolean {
  return config.environment === 'development'
}

export function isTest(): boolean {
  return config.environment === 'test'
}
