<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="[
      'button',
      `button--${variant}`,
      `button--${size}`,
      {
        'button--loading': loading,
        'button--full-width': fullWidth,
      },
    ]"
    @click="$emit('click')"
  >
    <span v-if="loading" class="button__spinner">⏳</span>
    <slot v-else />
  </button>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'small' | 'medium' | 'large'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
  fullWidth?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'secondary',
  size: 'medium',
  type: 'button',
  disabled: false,
  loading: false,
  fullWidth: false,
})

defineEmits<{
  click: []
}>()
</script>

<style scoped>
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  text-decoration: none;
  line-height: 1;
}

.button:disabled,
.button--loading {
  cursor: not-allowed;
  opacity: 0.7;
}

.button--full-width {
  width: 100%;
}

/* Sizes */
.button--small {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.button--medium {
  padding: 0.6rem 1.2rem;
  font-size: 0.95rem;
}

.button--large {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
}

/* Variants */
.button--primary {
  background: var(--button-background-color, var(--color-primary, #007acc));
  color: white;
  border-color: var(--button-background-color, var(--color-primary, #007acc));
}

.button--primary:hover:not(:disabled) {
  background: var(--button-hover-color, var(--color-primary-dark, #005a9e));
  border-color: var(--button-hover-color, var(--color-primary-dark, #005a9e));
}

.button--primary:active:not(:disabled) {
  background: var(--button-active-color, var(--color-primary-darker, #004080));
  border-color: var(--button-active-color, var(--color-primary-darker, #004080));
}

.button--secondary {
  background: var(--color-background);
  color: var(--color-text);
  border-color: var(--color-border);
}

.button--secondary:hover:not(:disabled) {
  background: var(--color-background-soft);
  border-color: var(--color-border-hover);
}

.button--secondary:active:not(:disabled) {
  background: var(--color-background-mute);
}

.button--danger {
  background: var(--color-error-soft, rgba(231, 76, 60, 0.1));
  color: var(--color-error, #e74c3c);
  border-color: var(--color-error, #e74c3c);
}

.button--danger:hover:not(:disabled) {
  background: var(--color-error, #e74c3c);
  color: white;
}

.button--ghost {
  background: transparent;
  color: var(--color-text);
  border-color: transparent;
}

.button--ghost:hover:not(:disabled) {
  background: var(--color-background-soft);
}

.button__spinner {
  font-size: 0.875em;
}
</style>
