import { ref, type Ref } from 'vue'
import { workflowService } from '@/services/workflowService'
import type { File } from '@/types'

export function useFileExplorer(workflowPath: Ref<string>) {
  const selectedFile = ref<File | undefined>(undefined)
  const fileContent = ref<string>('')
  const loadingFileContent = ref<boolean>(false)
  const error = ref<string>('')

  // Helper to find parent directory of a file
  function findParent(files: File[] | undefined, target: File): File | undefined {
    if (!files) return undefined

    for (const file of files) {
      if (file.isDirectory && file.files) {
        if (file.files.some((f) => f === target)) {
          return file
        }

        const nestedResult = findParent(file.files, target)
        if (nestedResult) {
          return nestedResult
        }
      }
    }
    return undefined
  }

  // Build full path to a file
  function buildFilePath(file: File, files: File[] | undefined): string {
    let path = file.name
    let parent = files ? findParent(files, file) : undefined

    while (parent) {
      path = `${parent.name}/${path}`
      parent = files ? findParent(files, parent) : undefined
    }

    return path
  }

  // Select a file and load its content
  async function selectFile(file: File, allFiles: File[]): Promise<void> {
    selectedFile.value = file

    // If it's a directory, don't load content
    if (file.isDirectory) return

    try {
      loadingFileContent.value = true
      fileContent.value = ''
      error.value = ''

      const filePath = buildFilePath(file, allFiles)
      fileContent.value = await workflowService.getFileContent(workflowPath.value, filePath)
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : String(err)
      console.error('Error loading file content:', err)
    } finally {
      loadingFileContent.value = false
    }
  }

  // Reset selection
  function clearSelection(): void {
    selectedFile.value = undefined
    fileContent.value = ''
  }

  return {
    selectedFile,
    fileContent,
    loadingFileContent,
    error,
    selectFile,
    clearSelection,
  }
}
