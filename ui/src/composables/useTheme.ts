import { ref, watchEffect } from 'vue'

const THEME_KEY = 'theme-preference'

export function useTheme() {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const saved = localStorage.getItem(THEME_KEY)
  const theme = ref(saved || (prefersDark ? 'theme-dark' : 'theme-light'))

  // Apply theme to <html>
  watchEffect(() => {
    document.documentElement.classList.remove('theme-light', 'theme-dark')
    document.documentElement.classList.add(theme.value)
  })

  function setTheme(newTheme: 'theme-light' | 'theme-dark') {
    theme.value = newTheme
    localStorage.setItem(THEME_KEY, newTheme)
  }

  function toggleTheme() {
    setTheme(theme.value === 'theme-dark' ? 'theme-light' : 'theme-dark')
  }

  // Listen for OS changes if no manual override
  if (!saved) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      setTheme(e.matches ? 'theme-dark' : 'theme-light')
    })
  }

  return { theme, setTheme, toggleTheme }
}
