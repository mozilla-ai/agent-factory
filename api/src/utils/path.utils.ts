import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const workflowsDir = path.resolve(__dirname, '../../../generated_workflows')

// Resolve workflow path based on path param
export function resolveWorkflowPath(workflowPath: string = ''): string {
  return path.join(workflowsDir, workflowPath)
}
