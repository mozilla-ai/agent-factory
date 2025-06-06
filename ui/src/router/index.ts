import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import WorkflowsView from '../views/WorkflowsView.vue'
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
    // Catch-all route for file paths
    path: '/workflows/:pathMatch(.*)*',
    name: 'file-view',
    component: FileView,
    // Add this to fix active class on parent route
    props: true,
  },
  { path: '/:pathMatch(.*)*', redirect: '/chat' }, // Redirect to home for any unmatched routes
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()

  // Restore from localStorage on refresh
  if (!auth.token && localStorage.getItem('token')) {
    auth.token = localStorage.getItem('token') || undefined
    // await auth.fetchUser()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if (to.path === '/login' && auth.isAuthenticated) {
    // Redirect to home page if the user is authenticated and tries to go to the login page
    next({ path: '/' }) // or any other page you want
  } else {
    next()
  }
})

export default router
