<template>
  <div class="file-explorer">
    <!-- File tree on the left -->
    <div class="file-tree-container">
      <h3>Files</h3>
      <div class="file-browser">
        <div class="custom-file-tree">
          <ul class="file-list">
            <template v-for="file in files" :key="file.name">
              <li
                class="file-item"
                :class="{
                  'file-item--directory': file.isDirectory,
                  'file-item--selected': selectedFile === file,
                }"
                @click="onSelect(file)"
              >
                <span class="file-icon">
                  <template v-if="file.isDirectory">📁</template>
                  <template v-else>📄</template>
                </span>
                <span class="file-name">{{ file.name }}</span>
              </li>
              <!-- Render nested files if directory is expanded -->
              <template v-if="file.isDirectory && selectedFile === file && file.files">
                <li
                  v-for="subFile in file.files"
                  :key="`${file.name}/${subFile.name}`"
                  class="file-item file-item--nested"
                  :class="{
                    'file-item--directory': subFile.isDirectory,
                    'file-item--selected': selectedFile === subFile,
                  }"
                  @click.stop="onSelect(subFile)"
                >
                  <span class="file-icon">
                    <template v-if="subFile.isDirectory">📁</template>
                    <template v-else>📄</template>
                  </span>
                  <span class="file-name">{{ subFile.name }}</span>
                </li>
              </template>
            </template>
          </ul>
        </div>
      </div>
    </div>

    <!-- File content on the right -->
    <div class="file-content-container">
      <div v-if="selectedFile && !selectedFile.isDirectory" class="file-content-header">
        <h3>{{ selectedFile.name }}</h3>
        <a v-if="downloadUrl" :href="downloadUrl" target="_blank" class="download-link">
          Download/View Raw
        </a>
      </div>
      <div v-else-if="selectedFile && selectedFile.isDirectory" class="file-content-header">
        <h3>Directory: {{ selectedFile.name }}</h3>
      </div>
      <div v-else class="file-content-header">
        <h3>Select a file to view its content</h3>
      </div>

      <!-- File content display -->
      <div class="file-content">
        <div v-if="loading" class="loading-file">Loading file content...</div>
        <div v-else-if="error" class="file-error">{{ error }}</div>
        <div v-else-if="selectedFile && !selectedFile.isDirectory">
          <pre class="code-preview">{{ content }}</pre>
        </div>
        <div v-else-if="selectedFile && selectedFile.isDirectory" class="directory-info">
          <p>This is a directory containing {{ selectedFile.files?.length || 0 }} items</p>
        </div>
        <div v-else class="no-file-selected">
          <p>No file selected. Click on a file in the tree to view its content.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'

// Define the File type directly here for clarity
interface File {
  name: string
  isDirectory: boolean
  files?: File[]
  path?: string
}

// Props definition
const props = defineProps({
  workflowId: {
    type: String,
    required: true,
  },
  files: {
    type: Array as PropType<File[]>,
    default: () => [],
  },
  selectedFile: {
    type: Object as PropType<File | undefined>,
    default: undefined,
  },
  content: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
})

// Events
const emit = defineEmits(['select'])

// Handle file selection
function onSelect(file: File) {
  emit('select', file)
}

// Generate download URL for the selected file
const downloadUrl = computed(() => {
  if (!props.selectedFile || props.selectedFile.isDirectory) return ''

  // Build the path based on directory structure if needed
  let filePath = props.selectedFile.name

  // If the file has an explicit path, use that instead
  if (props.selectedFile.path) {
    filePath = props.selectedFile.path
  }

  return `http://localhost:3000/agent-factory/workflows/${props.workflowId}/${filePath}`
})
</script>

<style scoped>
.file-explorer {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1rem;
  height: 60vh;
}

.file-tree-container,
.file-content-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-background-soft);
}

.file-tree-container h3,
.file-content-header h3 {
  margin: 0;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-mute);
}

.file-content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.download-link {
  margin-right: 1rem;
  font-size: 0.9rem;
  color: var(--color-primary);
  text-decoration: none;
}

.download-link:hover {
  text-decoration: underline;
}

.file-browser {
  flex: 1;
  overflow: auto;
  padding: 0.5rem;
}

.file-content {
  flex: 1;
  overflow: auto;
  padding: 1rem;
}

/* Custom file tree styles */
.custom-file-tree {
  font-family: monospace;
}

.file-list {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.file-item {
  padding: 0.4rem 0.6rem;
  margin: 0.1rem 0;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

.file-item:hover {
  background: var(--color-background);
}

.file-item--selected {
  background: var(--color-background-mute) !important;
}

.file-item--directory {
  font-weight: bold;
}

.file-item--nested {
  padding-left: 1.5rem;
}

.file-icon {
  margin-right: 0.5rem;
}

.file-name {
  word-break: break-all;
}

/* File content styles */
.code-preview {
  font-family: monospace;
  white-space: pre-wrap;
  padding: 0;
  margin: 0;
}

.loading-file,
.no-file-selected,
.directory-info,
.file-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-light);
}

.file-error {
  color: var(--color-error, red);
  text-align: center;
}

/* Media query for small screens */
@media (max-width: 768px) {
  .file-explorer {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
}
</style>
