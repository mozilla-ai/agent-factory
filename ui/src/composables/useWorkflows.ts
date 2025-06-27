import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import { workflowService } from '@/services/workflowService'
import { queryKeys } from '@/helpers/queryKeys'

/**
 * Simple composable to replace workflows store with TanStack Query
 * Provides automatic caching, refetching, and consistent state management
 */
export function useWorkflows() {
  const queryClient = useQueryClient()

  const workflowsQuery = useQuery({
    queryKey: queryKeys.workflows(),
    queryFn: workflowService.getWorkflows,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 1, // Only retry once to quickly show error state
  })

  // Get workflow by ID helper
  const getWorkflowById = (id: string) => {
    return workflowsQuery.data.value?.find((w) => w.name === id || w.path === id)
  }

  // Invalidate workflows cache (replaces manual store refresh)
  const invalidateWorkflows = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.workflows() })
  }

  return {
    workflows: computed(() => workflowsQuery.data.value || []),
    loading: workflowsQuery.isLoading,
    error: computed(() => workflowsQuery.error.value?.message || ''),
    getWorkflowById,
    invalidateWorkflows,
  }
}
