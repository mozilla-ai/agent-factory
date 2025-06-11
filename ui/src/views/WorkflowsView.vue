<template>
  <div class="workflows-container">
    <h1>Workflows</h1>

    <!-- Loading, error and empty states -->
    <div v-if="loading" class="loading">Loading workflows...</div>

    <div v-else-if="error" class="error">Error loading workflows: {{ error }}</div>

    <div v-else-if="workflows.length === 0" class="no-workflows">No workflows found.</div>

    <!-- Workflows list grid -->
    <div v-else class="workflows-grid">
      <div
        v-for="workflow in workflows"
        :key="workflow.name"
        class="workflow-item"
        @click="selectWorkflow(workflow)"
      >
        <div class="workflow-card">
          <h3>{{ workflow.name }}</h3>
          <p>{{ workflow.files?.length || 0 }} files</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowsStore } from '../stores/workflows'

const router = useRouter()
const workflowsStore = useWorkflowsStore()

// Compute state from store
const workflows = computed(() => workflowsStore.workflows)
const loading = computed(() => workflowsStore.loading)
const error = computed(() => workflowsStore.error)

// Navigate to the workflow details view - no direct API calls
function selectWorkflow(workflow: { name: string }) {
  router.push({
    name: 'workflow-details',
    params: { id: workflow.name },
  })
}

// Load workflows when the component is mounted
onMounted(async () => {
  if (workflows.value.length === 0) {
    await workflowsStore.loadWorkflows()
  }
})
</script>

<style scoped>
.workflows-container {
  display: flex;
  flex-direction: column;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.loading,
.error,
.no-workflows {
  display: flex;
  padding: 2rem;
  justify-content: center;
  align-items: center;
  color: var(--color-text-light);
  font-style: italic;
}

.error {
  color: var(--color-error, red);
}

.workflows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.workflow-item {
  cursor: pointer;
}

.workflow-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.5rem;
  border-radius: 8px;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  transition: all 0.3s;
}

.workflow-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--color-border-hover);
}
</style>
