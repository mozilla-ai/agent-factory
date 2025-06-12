import fs from 'node:fs/promises'
import path from 'node:path'
import type { FileEntry } from '../types/index.js'

/**
 * Helper to recursively list files and directories asynchronously
 * @param dirPath - Directory path to list
 * @returns List of files and directories with their metadata
 */
export async function listFilesRecursive(
  dirPath: string,
): Promise<FileEntry[]> {
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true })

    return Promise.all(
      entries.map(async (entry) => {
        const fullPath = path.join(dirPath, entry.name)

        if (entry.isDirectory()) {
          return {
            name: entry.name,
            isDirectory: true,
            files: await listFilesRecursive(fullPath),
          }
        } else {
          return {
            name: entry.name,
            isDirectory: false,
          }
        }
      }),
    )
  } catch (error) {
    console.error(`Failed to read directory ${dirPath}:`, error)
    return []
  }
}
