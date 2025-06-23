import { getErrorMessage } from './error.helpers'

export interface StreamProcessorCallbacks {
  onChunk: (chunk: string) => void
  onComplete?: () => void
  onError?: (error: string) => void
  onStart?: () => void
}

/**
 * Generic ReadableStream processor that lets components handle chunks however they need
 */
export async function processStream(
  stream: ReadableStream,
  callbacks: StreamProcessorCallbacks,
): Promise<void> {
  const { onChunk, onComplete, onError, onStart } = callbacks
  const reader = stream.getReader()
  const decoder = new TextDecoder()

  try {
    if (onStart) {
      onStart()
    }

    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      onChunk(chunk)
    }

    if (onComplete) {
      onComplete()
    }
  } catch (err) {
    const errorMessage = getErrorMessage(err)
    if (onError) {
      onError(errorMessage)
    }
    throw err
  } finally {
    reader.releaseLock()
  }
}

/**
 * Convenience function for simple string accumulation
 */
export async function processStreamToString(
  stream: ReadableStream,
  onChunk?: (chunk: string) => void,
): Promise<string> {
  let output = ''

  await processStream(stream, {
    onChunk: (chunk: string) => {
      output += chunk
      if (onChunk) {
        onChunk(chunk)
      }
    },
  })

  return output
}
