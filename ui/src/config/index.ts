// Environment-aware configuration
export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'

// Feature flags
export const features = {
  enableDevTools: import.meta.env.DEV,
  enableAutoRefresh: import.meta.env.VITE_ENABLE_AUTO_REFRESH === 'true',
}

// Application settings
export const settings = {
  autoRefreshInterval: Number(import.meta.env.VITE_AUTO_REFRESH_INTERVAL || 30000),
  maxFileSize: Number(import.meta.env.VITE_MAX_FILE_SIZE || 5000000), // 5MB default
}

// Routes
export const routes = {
  workflowList: '/workflows',
  workflowDetail: (id: string) => `/workflows/${id}`,
}
