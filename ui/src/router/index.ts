import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import WorkflowsView from '../views/WorkflowsView.vue'
import WorkflowDetailsView from '../views/WorkflowDetailsView.vue'
import FileView from '../views/FileView.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'home',
    redirect: '/chat',
    meta: { requiresAuth: false },
  },
  {
    path: '/chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { requiresAuth: false },
    name: 'Chat',
  },
  {
    path: '/workflows',
    name: 'workflows',
    component: WorkflowsView,
  },
  {
    // Specific workflow details page
    path: '/workflows/:id',
    name: 'workflow-details',
    component: WorkflowDetailsView,
    props: true,
  },
  {
    path: '/workflows/evaluate',
    name: 'agent-evaluation',
    component: () => import('@/views/AgentEvaluationView.vue'),
    meta: { requiresAuth: false },
  },
  {
    // Catch-all route for file paths - keep for legacy support
    path: '/workflows/:pathMatch(.*)*',
    name: 'file-view',
    component: FileView,
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Authentication guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
