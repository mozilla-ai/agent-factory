import fs from 'fs/promises'
import path from 'path'
import YAML from 'yaml'
import { getWorkflowPath } from '../config/index.js'
import {
  NotFoundError,
  FileOperationError,
} from '../middleware/error.middleware.js'
import type {
  FileEntry,
  WorkflowInfo,
  EvaluationCriteria,
  EvaluationResult,
} from '../types/index.js'
import { FILE_NAMES } from '../constants/index.js'

class FileService {
  // Check if file exists
  async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath)
      return true
    } catch {
      return false
    }
  }

  // Ensure directory exists
  async ensureDirectory(dirPath: string): Promise<void> {
    try {
      await fs.mkdir(dirPath, { recursive: true })
    } catch (error) {
      throw new FileOperationError(`Failed to create directory: ${dirPath}`, {
        error,
      })
    }
  }

  // List directory contents
  async listDirectory(dirPath: string): Promise<FileEntry[]> {
    try {
      const items = await fs.readdir(dirPath, { withFileTypes: true })
      const result: FileEntry[] = []

      for (const item of items) {
        result.push({
          name: item.name,
          isDirectory: item.isDirectory(),
        })
      }

      return result
    } catch (error) {
      throw new FileOperationError(`Failed to list directory: ${dirPath}`, {
        error,
      })
    }
  }

  // Get workflow information
  async getWorkflowInfo(workflowPath: string): Promise<WorkflowInfo> {
    const fullPath = getWorkflowPath(workflowPath)

    if (!(await this.fileExists(fullPath))) {
      throw new NotFoundError(`Workflow not found: ${workflowPath}`)
    }

    const agentPath = path.join(fullPath, FILE_NAMES.AGENT)
    const criteriaPath = path.join(fullPath, FILE_NAMES.EVALUATION_CASE)
    const resultsPath = path.join(fullPath, FILE_NAMES.EVALUATION_RESULTS)
    const tracePath = path.join(fullPath, FILE_NAMES.AGENT_EVAL_TRACE)

    let lastModified: Date | undefined
    try {
      const stats = await fs.stat(fullPath)
      lastModified = stats.mtime
    } catch {
      // Ignore errors getting modification time
    }

    return {
      name: path.basename(workflowPath),
      path: workflowPath,
      hasAgent: await this.fileExists(agentPath),
      hasEvaluationCriteria: await this.fileExists(criteriaPath),
      hasEvaluationResults: await this.fileExists(resultsPath),
      hasAgentTrace: await this.fileExists(tracePath),
      lastModified,
    }
  }

  // List all workflows
  async listWorkflows(): Promise<WorkflowInfo[]> {
    const workflowsDir = getWorkflowPath()

    if (!(await this.fileExists(workflowsDir))) {
      return []
    }

    try {
      const items = await fs.readdir(workflowsDir, { withFileTypes: true })
      const workflows: WorkflowInfo[] = []

      for (const item of items) {
        if (item.isDirectory()) {
          try {
            const workflow = await this.getWorkflowInfo(item.name)
            // Add files information like the original implementation
            const workflowFullPath = getWorkflowPath(item.name)
            const files = await this.listFilesRecursive(workflowFullPath)
            workflows.push({
              ...workflow,
              files,
              isDirectory: true,
            })
          } catch (error) {
            // Skip invalid workflows
            console.warn(`Skipping invalid workflow: ${item.name}`, error)
          }
        }
      }

      return workflows.sort((a, b) => a.name.localeCompare(b.name))
    } catch (error) {
      throw new FileOperationError('Failed to list workflows', { error })
    }
  }

  // Recursively list files in a directory (needed for workflow files)
  private async listFilesRecursive(dirPath: string): Promise<FileEntry[]> {
    try {
      const items = await fs.readdir(dirPath, { withFileTypes: true })
      const result: FileEntry[] = []

      for (const item of items) {
        if (item.isDirectory()) {
          const subItems = await this.listFilesRecursive(
            path.join(dirPath, item.name),
          )
          result.push({
            name: item.name,
            isDirectory: true,
            path: item.name,
          })
          // Add subdirectory files with prefixed paths
          for (const subItem of subItems) {
            result.push({
              ...subItem,
              path: path.join(item.name, subItem.path || subItem.name),
            })
          }
        } else {
          result.push({
            name: item.name,
            isDirectory: false,
            path: item.name,
          })
        }
      }

      return result
    } catch (error) {
      console.warn(`Could not list files in ${dirPath}:`, error)
      return []
    }
  }

  // Save evaluation criteria
  async saveEvaluationCriteria(
    workflowPath: string,
    criteria: EvaluationCriteria,
  ): Promise<string> {
    const fullPath = getWorkflowPath(workflowPath)
    await this.ensureDirectory(fullPath)

    const criteriaFilePath = path.join(fullPath, FILE_NAMES.EVALUATION_CASE)

    try {
      await fs.writeFile(criteriaFilePath, YAML.stringify(criteria), 'utf8')
      return criteriaFilePath
    } catch (error) {
      throw new FileOperationError('Failed to save evaluation criteria', {
        workflowPath,
        error,
      })
    }
  }

  // Load evaluation criteria
  async loadEvaluationCriteria(
    workflowPath: string,
  ): Promise<EvaluationCriteria> {
    const fullPath = getWorkflowPath(workflowPath)
    const criteriaFilePath = path.join(fullPath, FILE_NAMES.EVALUATION_CASE)

    if (!(await this.fileExists(criteriaFilePath))) {
      throw new NotFoundError(
        `Evaluation criteria not found for workflow: ${workflowPath}`,
      )
    }

    try {
      const content = await fs.readFile(criteriaFilePath, 'utf8')
      return YAML.parse(content) as EvaluationCriteria
    } catch (error) {
      throw new FileOperationError('Failed to load evaluation criteria', {
        workflowPath,
        error,
      })
    }
  }

  // Load evaluation results
  async loadEvaluationResults(workflowPath: string): Promise<EvaluationResult> {
    const fullPath = getWorkflowPath(workflowPath)
    const resultsFilePath = path.join(fullPath, FILE_NAMES.EVALUATION_RESULTS)

    if (!(await this.fileExists(resultsFilePath))) {
      throw new NotFoundError(
        `Evaluation results not found for workflow: ${workflowPath}`,
      )
    }

    try {
      const content = await fs.readFile(resultsFilePath, 'utf8')
      return JSON.parse(content) as EvaluationResult
    } catch (error) {
      throw new FileOperationError('Failed to load evaluation results', {
        workflowPath,
        error,
      })
    }
  }

  // Delete file (safe operation)
  async deleteFile(filePath: string): Promise<boolean> {
    try {
      await fs.unlink(filePath)
      return true
    } catch (error: unknown) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return false // File didn't exist
      }
      throw new FileOperationError(`Failed to delete file: ${filePath}`, {
        error,
      })
    }
  }

  // Delete workflow files
  async deleteAgentTrace(workflowPath: string): Promise<boolean> {
    const fullPath = getWorkflowPath(workflowPath)
    const tracePath = path.join(fullPath, FILE_NAMES.AGENT_EVAL_TRACE)
    return this.deleteFile(tracePath)
  }

  async deleteEvaluationCriteria(workflowPath: string): Promise<boolean> {
    const fullPath = getWorkflowPath(workflowPath)
    const criteriaPath = path.join(fullPath, FILE_NAMES.EVALUATION_CASE)
    return this.deleteFile(criteriaPath)
  }

  async deleteEvaluationResults(workflowPath: string): Promise<boolean> {
    const fullPath = getWorkflowPath(workflowPath)
    const resultsPath = path.join(fullPath, FILE_NAMES.EVALUATION_RESULTS)
    return this.deleteFile(resultsPath)
  }

  // Copy file
  async copyFile(source: string, destination: string): Promise<void> {
    try {
      await fs.copyFile(source, destination)
    } catch (error) {
      throw new FileOperationError(
        `Failed to copy file from ${source} to ${destination}`,
        { error },
      )
    }
  }

  // Read file content
  async readFile(filePath: string): Promise<string> {
    try {
      return await fs.readFile(filePath, 'utf8')
    } catch (error: unknown) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        throw new NotFoundError(`File not found: ${filePath}`)
      }
      throw new FileOperationError(`Failed to read file: ${filePath}`, {
        error,
      })
    }
  }

  // Write file content
  async writeFile(filePath: string, content: string): Promise<void> {
    try {
      await fs.writeFile(filePath, content, 'utf8')
    } catch (error) {
      throw new FileOperationError(`Failed to write file: ${filePath}`, {
        error,
      })
    }
  }
}

// Singleton instance
export const fileService = new FileService()
export { FileService }
