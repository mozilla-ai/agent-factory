<template>
  <form @submit.prevent="handleLogin" class="login-form" name="login-form">
    <h2 style="text-align: center; margin-bottom: 1rem">Mzai Platform</h2>
    <input v-model="email" placeholder="Email" :aria-required="true" required />
    <input
      v-model="password"
      type="password"
      placeholder="Password"
      :aria-required="true"
      required
    />
    <button type="submit" :disabled="loginMutation.isPending.value">Login</button>
    <div v-if="loginMutation.isError.value" class="error">
      {{ loginMutation.error.value?.message || 'Login failed' }}
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMutation } from '@tanstack/vue-query'

const email = ref<string>('')
const password = ref<string>('')
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const loginMutation = useMutation({
  mutationFn: authStore.login,
  onSuccess: () => {
    const redirectPath = (route.query.redirect as string) || '/'
    router.push(redirectPath)
  },
  onError: () => {
    alert('Login failed')
  },
})

const handleLogin = () => {
  loginMutation.mutate({ email: email.value, password: password.value })
}
</script>

<style scoped>
.login-form {
  display: flex;
  flex-direction: column;
  /* gap: 0.5rem; */
  width: 300px;
  margin: auto;
}
.login-form input {
  margin-bottom: 10px;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
}
</style>
