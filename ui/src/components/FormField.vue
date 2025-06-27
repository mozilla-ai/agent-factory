<template>
  <div class="form-group">
    <label v-if="label" :for="fieldId">{{ label }}</label>

    <select
      v-if="type === 'select'"
      :id="fieldId"
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      :required="required"
      :disabled="disabled"
      :class="{ 'input-error': hasError }"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>

    <textarea
      v-else-if="type === 'textarea'"
      :id="fieldId"
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :rows="rows"
      :class="{ 'input-error': hasError }"
    ></textarea>

    <input
      v-else
      :id="fieldId"
      :type="type"
      :value="modelValue"
      @input="handleInput"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :min="min"
      :max="max"
      :step="step"
      :class="{ 'input-error': hasError }"
    />

    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
interface Option {
  value: string | number
  label: string
}

interface Props {
  modelValue?: string | number
  label?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea'
  placeholder?: string
  required?: boolean
  disabled?: boolean
  error?: string
  fieldId?: string
  // Select specific
  options?: Option[]
  // Textarea specific
  rows?: number
  // Number input specific
  min?: number
  max?: number
  step?: number
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  required: false,
  disabled: false,
  rows: 3,
})

const hasError = computed(() => !!props.error)

// Handle input with proper type conversion
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = target.value

  if (props.type === 'number') {
    // Convert to number for number inputs
    const numValue = value === '' ? 0 : Number(value)
    emit('update:modelValue', numValue)
  } else {
    // Keep as string for other input types
    emit('update:modelValue', value)
  }
}

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

// Generate a field ID if not provided
const fieldId = computed(() => props.fieldId || `field-${Math.random().toString(36).substr(2, 9)}`)
</script>

<script lang="ts">
import { computed } from 'vue'
</script>

<style scoped>
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-weight: 500;
  color: var(--color-text);
}

input,
textarea,
select {
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background-color: var(--color-background);
  color: var(--color-text);
  font-family: inherit;
  font-size: 1rem;
  transition: border-color 0.2s ease;
}

input:focus,
textarea:focus,
select:focus {
  outline: 2px solid var(--color-border-hover);
  border-color: var(--color-border-hover);
}

input:disabled,
textarea:disabled,
select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: var(--color-background-mute);
}

.input-error {
  border-color: var(--color-error) !important;
  background-color: var(--color-error-soft) !important;
}

.error-message {
  color: var(--color-error);
  font-size: 0.8rem;
  margin-top: 0.25rem;
}
</style>
