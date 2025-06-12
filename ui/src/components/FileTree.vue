<template>
  <div class="custom-file-tree">
    <ul class="file-list">
      <template v-for="file in files" :key="file.name">
        <li
          class="file-item"
          :class="{
            'file-item--directory': file.isDirectory,
            'file-item--selected': selectedFile === file,
          }"
          @click="selectFile(file)"
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
            @click.stop="selectFile(subFile)"
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
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import type { WorkflowFile } from '@/types'

defineProps<{
  files: WorkflowFile[]
  selectedFile: WorkflowFile | undefined
}>()

const emit = defineEmits<{
  (e: 'select', file: WorkflowFile): void
}>()

function selectFile(file: WorkflowFile) {
  emit('select', file)
}
</script>

<style scoped>
.custom-file-tree {
  /* Add any custom styles for the file tree component here */
}

.file-list {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.file-item:hover {
  background-color: var(--color-background-soft, #f5f5f5);
}

.file-item--directory {
  font-weight: bold;
}

.file-item--selected {
  background-color: var(--color-primary-light, #e0f7fa);
}

.file-icon {
  margin-right: 8px;
}

.file-name {
  flex-grow: 1;
}

/* Nested file styles */
.file-item--nested {
  padding-left: 24px;
}
</style>
