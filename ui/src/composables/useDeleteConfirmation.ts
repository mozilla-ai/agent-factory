import { ref } from 'vue'

export interface DeleteConfirmationOptions {
  title: string
  message: string
  confirmButtonText?: string
  isDangerous?: boolean
}

interface DeleteConfirmationState {
  title: string
  message: string
  confirmButtonText: string
  isDangerous: boolean
}

export function useDeleteConfirmation() {
  const showDeleteDialog = ref(false)
  const deleteOptions = ref<DeleteConfirmationState>({
    title: '',
    message: '',
    confirmButtonText: 'Delete',
    isDangerous: true,
  })

  function openDeleteDialog(options: DeleteConfirmationOptions) {
    deleteOptions.value = {
      confirmButtonText: 'Delete',
      isDangerous: true,
      ...options,
    }
    showDeleteDialog.value = true
  }

  function closeDeleteDialog() {
    showDeleteDialog.value = false
  }

  return {
    showDeleteDialog,
    deleteOptions,
    openDeleteDialog,
    closeDeleteDialog,
  }
}
