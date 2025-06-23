// stores/auth.ts
import router from '@/router'
import { jwtDecode } from 'jwt-decode'
import { defineStore } from 'pinia'

// Types
interface User {
  id: number
  email: string
  name: string
}

interface Credentials {
  email: string
  password: string
}

interface JwtPayload {
  exp: number
}

interface TokenResponse {
  access: string
  refresh: string
}

// Constants
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'
const TOKEN_EXPIRY_THRESHOLD = 60 // Seconds before expiry to refresh token
const STORAGE_KEYS = {
  TOKEN: 'token',
  REFRESH_TOKEN: 'refreshToken',
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(STORAGE_KEYS.TOKEN) || undefined,
    refreshToken: localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN) || undefined,
    user: undefined as User | undefined,
  }),

  getters: {
    isAuthenticated(): boolean {
      return !!this.token
    },

    // Get authorization header for axios
    authHeader(): Record<string, string> {
      return this.token ? { Authorization: `Bearer ${this.token}` } : {}
    },
  },

  actions: {
    /**
     * Log in user with email and password
     */
    async login(credentials: Credentials): Promise<void> {
      const response = await fetch(`${API_BASE_URL}/token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Login failed: ${response.status}`)
      }

      const data = (await response.json()) as TokenResponse
      this.setTokens(data.access, data.refresh)
    },

    /**
     * Log out user
     */
    logout(): void {
      this.token = undefined
      this.refreshToken = undefined
      this.user = undefined
      localStorage.removeItem(STORAGE_KEYS.TOKEN)
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
      router.push({ name: 'Login' }) // Redirect to login page
    },

    /**
     * Set authentication tokens and save to localStorage
     */
    setTokens(access: string, refresh: string): void {
      this.token = access
      this.refreshToken = refresh
      localStorage.setItem(STORAGE_KEYS.TOKEN, access)
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refresh)
    },

    /**
     * Check if token is expired
     */
    isTokenExpired(token: string): boolean {
      try {
        const { exp } = jwtDecode<JwtPayload>(token)
        const now = Math.floor(Date.now() / 1000)
        return exp <= now
      } catch {
        return true
      }
    },

    /**
     * Check if token will expire soon (within threshold)
     */
    willTokenExpireSoon(token: string): boolean {
      try {
        const { exp } = jwtDecode<JwtPayload>(token)
        const now = Math.floor(Date.now() / 1000)
        return exp - now < TOKEN_EXPIRY_THRESHOLD
      } catch {
        return true
      }
    },

    /**
     * Refresh the access token using the refresh token
     * Returns the new access token or throws an error
     */
    async doRefreshToken(): Promise<string> {
      if (!this.refreshToken) {
        throw new Error('No refresh token available')
      }

      const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: this.refreshToken }),
      })

      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.status}`)
      }

      const data = (await response.json()) as TokenResponse
      this.token = data.access
      localStorage.setItem(STORAGE_KEYS.TOKEN, data.access)

      return data.access
    },

    /**
     * Get a valid token for API requests
     * Returns the current token, refreshes if needed, or throws an error if authentication fails
     */
    async getValidToken(): Promise<string> {
      // No token or refresh token available
      if (!this.token || !this.refreshToken) {
        // throw new Error('No authentication tokens available')
        this.logout()
        return ''
      }

      // Token expired completely - need to refresh
      if (this.isTokenExpired(this.token)) {
        return this.doRefreshToken()
      }

      // Token will expire soon - refresh in background but don't wait for it
      if (this.willTokenExpireSoon(this.token)) {
        this.doRefreshToken().catch(() => {
          // Silent background refresh - errors handled by consumer on next request
        })
      }

      // Return current token
      return this.token
    },
  },
})
