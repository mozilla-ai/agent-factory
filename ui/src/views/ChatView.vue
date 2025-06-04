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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const prompt = ref<string>('Summarize text content from a given webpage URL')
const response = ref<string>('')
const isLoading = ref<boolean>(false)

const handleSendClicked = async () => {
  try {
    response.value = ''
    isLoading.value = true

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
    isLoading.value = false
  } catch (err) {
    console.error('Error in generate:', err)
    response.value += '\n\nError occurred: ' + err.message
    isLoading.value = false
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
}

.output {
  max-height: 800px;
  overflow-y: auto;
  /* background: #f9f9f9; */
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid var(--border-color);
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
</style>
