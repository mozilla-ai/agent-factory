import { ref, readonly } from 'vue'
import { processStream as processStreamHelper } from '@/helpers/stream.helpers'

/**
 * Composable for processing ReadableStream responses from API endpoints
 */
export function useStreamProcessor() {
  const isProcessing = ref(false)
  const output = ref('')
  const error = ref('')

  /**
   * Process a ReadableStream and accumulate text output
   */
  async function processStream(
    stream: ReadableStream,
    onChunk?: (chunk: string) => void,
    onComplete?: () => void,
  ): Promise<void> {
    await processStreamHelper(stream, {
      onStart: () => {
        isProcessing.value = true
        error.value = ''
      },
      onChunk: (chunk: string) => {
        output.value += chunk
        if (onChunk) {
          onChunk(chunk)
        }
      },
      onComplete: () => {
        isProcessing.value = false
        if (onComplete) {
          onComplete()
        }
      },
      onError: (errorMessage: string) => {
        error.value = errorMessage
        output.value += `\nError: ${errorMessage}`
        isProcessing.value = false
      },
    })
  }

  /**
   * Clear output and error state
   */
  function clearOutput() {
    output.value = ''
    error.value = ''
  }

  /**
   * Set initial output message
   */
  function setInitialMessage(message: string) {
    output.value = message
  }

  return {
    isProcessing: readonly(isProcessing),
    output: readonly(output),
    error: readonly(error),
    processStream,
    clearOutput,
    setInitialMessage,
  }
}
