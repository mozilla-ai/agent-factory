import { useRouter } from 'vue-router'

export function useNavigation() {
  const router = useRouter()

  const navigateToTab = (tab: string, workflowId?: string) => {
    const currentPath = router.currentRoute.value.path
    const currentQuery = router.currentRoute.value.query

    router.push({
      path: workflowId ? `/workflows/${workflowId}` : currentPath,
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

  const navigateToEvaluate = (workflowId: string) => {
    navigateToTab('evaluate', workflowId)
  }

  const navigateToTrace = (workflowId: string) => {
    navigateToTab('agent-trace', workflowId)
  }

  const navigateToCriteria = (workflowId: string) => {
    navigateToTab('criteria', workflowId)
  }

  const navigateToResults = (workflowId: string) => {
    navigateToTab('results', workflowId)
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
