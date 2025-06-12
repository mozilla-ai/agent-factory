import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Resolve workflow path based on path param (latest or archive/<workflow_id>)
export function resolveWorkflowPath(workflowPath: string): string {
  const workflowsDir = path.resolve(__dirname, '../../../generated_workflows')

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
