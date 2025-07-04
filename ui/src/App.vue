<template>
  <div class="app">
    <VueQueryDevtools />

    <nav class="global-nav">
      <router-link to="/chat" class="nav-link">Home</router-link>
      <router-link to="/workflows" class="nav-link">Workflows</router-link>
    </nav>

    <button class="logout-button" v-if="authStore.isAuthenticated" type="button" @click="logout">
      Logout
    </button>
    <button
      class="theme-switcher"
      @click="toggleTheme"
      :aria-label="theme === 'theme-dark' ? 'Switch to light mode' : 'Switch to dark mode'"
    >
      <span v-if="theme === 'theme-dark'" class="icon">
        <!-- Sun icon -->
        <svg
          width="1rem"
          height="1rem"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="12" cy="12" r="5" />
          <path
            d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
          />
        </svg>
      </span>
      <span v-else class="icon">
        <!-- Moon icon -->
        <svg
          width="1rem"
          height="1rem"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z" />
        </svg>
      </span>
    </button>
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { VueQueryDevtools } from '@tanstack/vue-query-devtools'
import { useAuthStore } from './stores/auth'
import { useTheme } from '@/composables/useTheme'

const authStore = useAuthStore()
const { theme, toggleTheme } = useTheme()

const logout = () => {
  authStore.logout()
}
</script>

<style scoped>
.global-nav {
  position: fixed;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 1.5rem;
  width: 100%;
  justify-content: center;
  padding: 1rem;
  z-index: 20;
  background-color: var(--color-background-soft);
}

.nav-link {
  text-decoration: none;
  color: var(--color-text);
  font-weight: 500;
  position: relative;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  transition: all 0.3s;
}

.nav-link:hover {
  background-color: var(--button-hover-color);
}

.nav-link.router-link-active {
  color: var(--color-primary);
}

.nav-link.router-link-active::after {
  content: '';
  position: absolute;
  bottom: -3px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: var(--color-primary);
}

.logout-button {
  position: absolute;
  top: 0;
  right: 0;
}

.back-button {
  position: absolute;
  top: 0;
  left: 0;
}

.theme-switcher {
  position: absolute;
  top: 0rem;
  right: 7rem;
  z-index: 10;
}

.theme-switcher.outline {
  border: 1px solid currentColor;
  border-radius: 0.25rem;
}

.app {
  display: flex;
  flex-direction: column;
  flex: 1;
}
</style>
