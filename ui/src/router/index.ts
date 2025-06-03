import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: Array<RouteRecordRaw> = [
  // { path: '/login', component: () => import('@/views/LoginView.vue'), name: 'Login' },
  {
    path: '/chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { requiresAuth: false },
    name: 'Chat',
  },
  { path: '/:pathMatch(.*)*', redirect: '/chat' }, // Redirect to home for any unmatched routes
]

const router = createRouter({
  history: createWebHistory(),
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
