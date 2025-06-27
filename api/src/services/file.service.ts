import fs from 'fs/promises'
import path from 'path'
import { getWorkflowPath } from '../config/index.js'
import type {
  FileEntry,
  WorkflowInfo,
  EvaluationCriteria,
  EvaluationResult,
  } from '../types/index.js'

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
    } catch {
      throw new Error(`Failed to create directory: ${dirPath}`)
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
    } catch {
      throw new Error(`Failed to list directory: ${dirPath}`)
    }
  }

  // Get workflow information
  async getWorkflowInfo(workflowPath: string): Promise<WorkflowInfo> {
    const fullPath = getWorkflowPath(workflowPath)

    if (!(await this.fileExists(fullPath))) {
      throw new Error(`Workflow not found: ${workflowPath}`)
    }

    const agentPath = path.join(fullPath, 'agent.py')
    const criteriaPath = path.join(fullPath, 'evaluation_case.json')
    const resultsPath = path.join(fullPath, 'evaluation_results.json')
    const tracePath = path.join(fullPath, 'agent_eval_trace.json')

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

      return workflows.sort((a, b) => b.name.localeCompare(a.name))
    } catch {
      throw new Error('Failed to list workflows')
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

  // Save evaluation criteria - now saves as JSON in the new simple format
  async saveEvaluationCriteria(
    workflowPath: string,
    criteria: EvaluationCriteria,
  ): Promise<string> {
    try {
      const fullPath = getWorkflowPath(workflowPath)
      console.log(`Saving criteria to path: ${fullPath}`)

      await this.ensureDirectory(fullPath)

      const criteriaFilePath = path.join(fullPath, 'evaluation_case.json')
      console.log(`Writing criteria file: ${criteriaFilePath}`)

      // Transform to the new simple format that Python expects
      const newFormat = {
        criteria: criteria.checkpoints.map(checkpoint => checkpoint.criteria)
      }

      await fs.writeFile(criteriaFilePath, JSON.stringify(newFormat, null, 2), 'utf8')
      console.log(
        `Successfully saved evaluation criteria to: ${criteriaFilePath}`,
      )

      return criteriaFilePath
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error)
      console.error('Error saving evaluation criteria:', {
        workflowPath,
        error: errorMessage,
        criteria: criteria,
      })
      throw new Error(
        `Failed to save evaluation criteria to ${workflowPath}: ${errorMessage}`,
      )
    }
  }

  // Load evaluation criteria - handles both current and future JSON formats
  async loadEvaluationCriteria(
    workflowPath: string,
  ): Promise<EvaluationCriteria> {
    const fullPath = getWorkflowPath(workflowPath)
    const criteriaFilePath = path.join(fullPath, 'evaluation_case.json')

    if (!(await this.fileExists(criteriaFilePath))) {
      throw new Error(
        `Evaluation criteria not found for workflow: ${workflowPath}`,
      )
    }

    try {
      const content = await fs.readFile(criteriaFilePath, 'utf8')
      const jsonData = JSON.parse(content)

      // Handle different JSON formats
      if (this.isEnhancedFormat(jsonData)) {
        // Future enhanced format with potential points and llm_judge
        return {
          llm_judge: jsonData.llm_judge || 'gpt-4.1',
          checkpoints: jsonData.criteria.map((item: any) => ({
            criteria: item.criteria,
            points: item.points || 0, // Use provided points or fallback to 0
          }))
        }
      } else if (this.isSimpleFormat(jsonData)) {
        // Current simple format with just criteria array
        return {
          llm_judge: 'gpt-4.1', // Default value
          checkpoints: jsonData.criteria.map((criterion: string) => ({
            criteria: criterion,
            points: 0, // Default points value
          }))
        }
      } else {
        // Assume it's already in the correct format (legacy or manual)
        return jsonData as EvaluationCriteria
      }
    } catch (error) {
      throw new Error('Failed to load evaluation criteria')
    }
  }

  // Helper method to check if it's the enhanced format
  private isEnhancedFormat(data: any): boolean {
    return Array.isArray(data.criteria) &&
           data.criteria.length > 0 &&
           typeof data.criteria[0] === 'object' &&
           'criteria' in data.criteria[0]
  }

  // Helper method to check if it's the simple format
  private isSimpleFormat(data: any): boolean {
    return Array.isArray(data.criteria) &&
           data.criteria.length > 0 &&
           typeof data.criteria[0] === 'string'
  }

  // Load evaluation results
  async loadEvaluationResults(workflowPath: string): Promise<EvaluationResult> {
    const fullPath = getWorkflowPath(workflowPath)
    const resultsFilePath = path.join(fullPath, 'evaluation_results.json')

    if (!(await this.fileExists(resultsFilePath))) {
      throw new Error(
        `Evaluation results not found for workflow: ${workflowPath}`,
      )
    }

    try {
      const content = await fs.readFile(resultsFilePath, 'utf8')
      return JSON.parse(content) as EvaluationResult
    } catch {
      throw new Error('Failed to load evaluation results')
    }
  }

  // Delete a file
  async deleteFile(filePath: string): Promise<boolean> {
    try {
      await fs.unlink(filePath)
      return true
    } catch {
      throw new Error(`Failed to delete file: ${filePath}`)
    }
  }

  // Delete agent trace file and invalidate evaluation results
  async deleteAgentTrace(workflowPath: string): Promise<boolean> {
    const fullPath = getWorkflowPath(workflowPath)
    const tracePath = path.join(fullPath, 'agent_eval_trace.json')

    try {
      await this.deleteFile(tracePath)

      // Delete evaluation results since they're now invalid without the agent trace
      const resultsPath = path.join(fullPath, 'evaluation_results.json')
      if (await this.fileExists(resultsPath)) {
        try {
          await this.deleteFile(resultsPath)
          console.log(
            `Deleted dependent evaluation results file: ${resultsPath}`,
          )
        } catch {
          console.warn(`Failed to delete dependent evaluation results`)
        }
      }

      return true
    } catch {
      return false
    }
  }

  // Delete evaluation criteria file and invalidate evaluation results
  async deleteEvaluationCriteria(workflowPath: string): Promise<boolean> {
    const fullPath = getWorkflowPath(workflowPath)
    const criteriaPath = path.join(fullPath, 'evaluation_case.json')

    try {
      await this.deleteFile(criteriaPath)

      // Delete evaluation results since they're now invalid without the criteria
      const resultsPath = path.join(fullPath, 'evaluation_results.json')
      if (await this.fileExists(resultsPath)) {
        try {
          await this.deleteFile(resultsPath)
          console.log(
            `Deleted dependent evaluation results file: ${resultsPath}`,
          )
        } catch {
          console.warn(`Failed to delete dependent evaluation results`)
        }
      }

      return true
    } catch {
      return false
    }
  }

  // Delete evaluation results file
  async deleteEvaluationResults(workflowPath: string): Promise<boolean> {
    const fullPath = getWorkflowPath(workflowPath)
    const resultsPath = path.join(fullPath, 'evaluation_results.json')
    return this.deleteFile(resultsPath)
  }

  // Copy file
  async copyFile(source: string, destination: string): Promise<void> {
    try {
      await fs.copyFile(source, destination)
    } catch {
      throw new Error(`Failed to copy file from ${source} to ${destination}`)
    }
  }

  // Read file
  async readFile(filePath: string): Promise<string> {
    try {
      if (!(await this.fileExists(filePath))) {
        throw new Error(`File not found: ${filePath}`)
      }
      return await fs.readFile(filePath, 'utf8')
    } catch (error) {
      if (error instanceof Error && error.message.includes('File not found')) {
        throw error
      }
      throw new Error(`Failed to read file: ${filePath}`)
    }
  }

  // Write file
  async writeFile(filePath: string, content: string): Promise<void> {
    try {
      await fs.writeFile(filePath, content, 'utf8')
    } catch {
      throw new Error(`Failed to write file: ${filePath}`)
    }
  }


}

// Singleton instance
export const fileService = new FileService()
export { FileService }
