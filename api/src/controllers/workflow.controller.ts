import { Request, Response } from 'express'
import path from 'node:path'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { listFilesRecursive } from '../utils/file.utils.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// List all generated workflows and their files
export async function listWorkflows(
  _req: Request,
  res: Response,
): Promise<void> {
  const workflowsDir = path.resolve(__dirname, '../../../generated_workflows')

  try {
    // Check if directory exists first
    try {
      await fs.access(workflowsDir)
    } catch {
      console.log('Workflows directory does not exist, returning empty array')
      res.json([])
      return
    }

    // Directory exists, read its contents
    const entries = await fs.readdir(workflowsDir, { withFileTypes: true })

    // If no entries or no directories, return empty array
    if (entries.length === 0 || !entries.some((entry) => entry.isDirectory())) {
      res.json([])
      return
    }

    const result = await Promise.all(
      entries
        .filter((entry) => entry.isDirectory())
        .map(async (entry) => ({
          name: entry.name,
          isDirectory: true,
          files: await listFilesRecursive(path.join(workflowsDir, entry.name)),
        })),
    )

    res.json(result)
  } catch (error) {
    console.error('Unexpected error reading workflows directory:', error)
    res.status(500).json({ error: 'Failed to read workflows directory' })
  }
}
