import { useRouter } from 'vue-router'

export function useNavigation() {
  const router = useRouter()

  const navigateToTab = (tab: string, workflowId?: string) => {
    const currentPath = router.currentRoute.value.path
    const currentQuery = router.currentRoute.value.query

    router.push({
      path: currentPath, // Always stay on current path
      query: { ...currentQuery, tab },
    })
  }

  const navigateToWorkflow = (workflowId: string, tab?: string) => {
    router.push({
      path: `/workflows/${workflowId}`,
      query: tab ? { tab } : {},
    })
  }

  const navigateToWorkflows = () => {
    router.push('/workflows')
  }

  const navigateToEvaluate = (workflowId?: string) => {
    navigateToTab('evaluate')
  }

  const navigateToTrace = (workflowId?: string) => {
    navigateToTab('agent-trace')
  }

  const navigateToCriteria = (workflowId?: string) => {
    navigateToTab('criteria')
  }

  const navigateToResults = (workflowId?: string) => {
    navigateToTab('results')
  }

  return {
    navigateToTab,
    navigateToWorkflow,
    navigateToWorkflows,
    navigateToEvaluate,
    navigateToTrace,
    navigateToCriteria,
    navigateToResults,
  }
}
