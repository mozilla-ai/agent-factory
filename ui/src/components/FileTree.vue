<template>
  <div class="file-tree-item">
    <div class="file-label" @click="handleClick">
      <span v-if="item.isDirectory" class="directory-icon">
        {{ isExpanded ? '📂' : '📁' }}
      </span>
      <span v-else class="file-icon">📄</span>
      <span class="item-name">{{ item.name }}</span>
      <span v-if="item.isDirectory && item.files" class="item-count">
        ({{ item.files.length }} items)
      </span>
    </div>
    <transition name="fade">
      <ul
        v-if="item.isDirectory && item.files && item.files.length > 0 && isExpanded"
        class="sub-items"
      >
        <li v-for="subItem in item.files" :key="subItem.name" class="sub-item">
          <FileTree :item="subItem" :path="path + '/' + item.name" />
        </li>
      </ul>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

// For recursive self-reference in <script setup>
defineOptions({
  name: 'FileTree',
})

const props = defineProps<{
  item: {
    name: string
    isDirectory: boolean
    files?: any[]
  }
  path?: string
}>()

// Default path is empty
const path = props.path || ''
const router = useRouter()
const isExpanded = ref(false)

const handleClick = () => {
  if (props.item.isDirectory) {
    // Toggle expansion of directory
    isExpanded.value = !isExpanded.value
  } else {
    // Navigate to file view when a file is clicked
    const filePath = `${path}/${props.item.name}`.replace(/^\/+/, '')
    router.push(`/workflows/${filePath}`)
  }
}
</script>

<style scoped>
.file-tree-item {
  margin: 4px 0;
}

.file-label {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  user-select: none;
}

.file-label:hover {
  background-color: var(--color-background-soft, #f5f5f5);
}

.item-name {
  margin-left: 4px;
}

.item-count {
  font-size: 0.85em;
  color: #888;
  margin-left: 4px;
}

.sub-items {
  margin-left: 20px;
  list-style-type: none;
  padding-left: 0;
}

.sub-item {
  background: transparent;
  box-shadow: none;
  padding: 0;
  margin: 0;
  cursor: default;
  border-radius: 0;
}

.sub-item:hover {
  background: transparent;
  box-shadow: none;
}

.directory-icon,
.file-icon {
  display: inline-block;
  width: 20px;
}

/* Transition animation */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
