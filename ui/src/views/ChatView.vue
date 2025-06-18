<template>
  <div class="agent-builder">
    <div class="chat-container">
      <div class="chat-header">
        <h1>Chat with Agent</h1>
      </div>
      <div class="chat-messages">
        <p>Welcome to the chat! How can I assist you today?</p>
      </div>
      <div class="chat-input">
        <textarea
          name="prompt"
          id="prompt"
          required
          :aria-required="true"
          v-model="prompt"
          placeholder="Type your prompt here..."
          rows="10"
          cols="70"
          class="text-area"
        ></textarea>
        <button @click="handleSendClicked">Send</button>
      </div>
    </div>
    <div class="output-container">
      <h2>Output</h2>
      <p v-if="!response">This is where the output will be displayed.</p>
      <p v-if="isLoading">Loading...</p>
      <pre v-if="response" class="output">{{ response }}</pre>

      <router-link
        v-if="generationComplete"
        :to="{ name: 'workflow-details', params: { id: 'latest' } }"
        class="view-files-link"
      >
        📁 View Generated Workflow
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useWorkflowsStore } from '@/stores/workflows'
import { useQueryClient } from '@tanstack/vue-query'
import { ref } from 'vue'

const prompt = ref<string>('Summarize text content from a given webpage URL')
const response = ref<string>('')
const isLoading = ref<boolean>(false)
const generationComplete = ref<boolean>(false)
const workflowsStore = useWorkflowsStore()
const queryClient = useQueryClient()

const handleSendClicked = async () => {
  try {
    response.value = ''
    isLoading.value = true
    generationComplete.value = false

    const res = await fetch(
      `http://localhost:3000/agent-factory?prompt=${encodeURIComponent(prompt.value)}`,
      {
        method: 'GET',
      },
    )

    if (!res.ok) {
      response.value = `Error: ${res.status} ${res.statusText}`
      isLoading.value = false
      return
    }

    const reader = res.body?.getReader()
    if (!reader) {
      response.value = 'Error: No response body'
      isLoading.value = false
      return
    }

    // Read streaming response
    const decoder = new TextDecoder()

    let done = false
    while (!done) {
      const { value, done: streamDone } = await reader.read()
      if (value) {
        const chunk = decoder.decode(value, { stream: true })
        response.value += chunk
      }
      done = streamDone
    }

    // Check if generation was successful
    if (response.value.includes('Workflow completed successfully')) {
      generationComplete.value = true

      // clear all queries cache
      workflowsStore.loadWorkflows()
      queryClient.invalidateQueries({
        queryKey: ['evaluation-criteria', 'latest'],
      })
      queryClient.invalidateQueries({
        queryKey: ['evaluation-status', 'latest'],
      })
      queryClient.invalidateQueries({
        queryKey: ['evaluation-results', 'latest'],
      })
      queryClient.invalidateQueries({
        queryKey: ['agentEvalTrace', 'latest'],
      })
      queryClient.invalidateQueries({
        queryKey: ['file-content', 'latest'],
      })
    }

    isLoading.value = false
  } catch (error: unknown) {
    isLoading.value = false
    const errorMessage = error instanceof Error ? error.message : String(error)
    response.value += '\n\nError occurred: ' + errorMessage
  }
}
</script>

<style scoped>
.agent-builder {
  display: flex;
  gap: 2rem;
  align-items: center; /* Vertical centering */
  justify-content: center; /* Horizontal centering */
  height: 100vh /* Full viewport height */;
  padding: 4rem;
  /* margin: 0 auto; */
}

.chat-container {
  flex: 1;
  padding-right: 2rem;
  border-right: 1px solid #ccc;
}

.output-container {
  flex: 1;
  /* padding: 20px; */
  justify-content: center;
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 80vh;
}

.output {
  height: 100%;
  max-height: 600px;
  overflow-y: auto;
  background: var(--color-background-soft, #f8f8f8); /* Lighter background similar to textarea */
  padding: 1rem;
  border-radius: 4px;
  /* border: 1px solid var(--border-color, #ccc); */
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 1rem;
}

.text-area {
  resize: vertical;
  padding: 0.75rem;
  border: 1px solid var(--color-border, #ccc);
  border-radius: 4px;
  font-family: inherit;
  background: var(--color-background-soft, #f8f8f8);
}

.chat-header {
  margin-bottom: 20px;
}

.chat-input {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chat-messages {
  height: 100px;
  overflow-y: auto;
  border: 1px solid #ccc;
  padding: 10px;
  margin-bottom: 20px;
}

.view-files-link {
  display: inline-block;
  margin-top: 15px;
  text-decoration: none;
  color: var(--color-text);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  background: var(--color-background-soft, #f8f8f8);
  border: 1px solid var(--color-border, #ccc);
  font-family: inherit;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}

.view-files-link:hover {
  background: var(--color-background-mute, #e8e8e8);
  border-color: var(--color-border-hover, #aaa);
}
</style>
