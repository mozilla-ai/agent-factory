import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import {VitePWA} from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  server: {
    host: '0.0.0.0', // Binds to all interfaces
    port: 5173, // Default Vite port
    hmr: {
      host: 'localhost', // Ensure HMR works in dev
    },
  },
  plugins: [
    vue(),
    vueDevTools(),
    VitePWA({
      registerType: 'autoUpdate', // Automatically update service worker when there's a new version
      manifest: false, // Disable manifest (not needed for caching only)
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,webp,svg}']
      },
      /* enable sw on development */
      // devOptions: {
      //   enabled: true
      //   /* other options */
      // }
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
