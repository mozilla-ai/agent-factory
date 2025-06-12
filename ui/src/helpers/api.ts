// import axios, { type InternalAxiosRequestConfig } from 'axios'
// import { useAuthStore } from '@/stores/auth'

// export const api = axios.create({
//   baseURL: import.meta.env.VITE_APP_API_BASE_URL,
// })

// // Request interceptor
// api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
//   const auth = useAuthStore()
//   try {
//     const token = await auth.getValidToken()

//     if (token) {
//       config.headers.Authorization = `Bearer ${token}`
//     }

//     return config
//   } catch {
//     auth.logout()
//     return config
//   }
// })

// // Response interceptor for 401 errors
// api.interceptors.response.use(
//   (response) => response,
//   (error) => {
//     if (error.response?.status === 401) {
//       const auth = useAuthStore()
//       auth.logout()
//       // Redirect to login page or show login modal
//     }
//     return Promise.reject(error)
//   },
// )
