import { useRouter } from 'vue-router'

export function useNavigation() {
  const router = useRouter()

  const navigateToTab = (tab: string, _workflowId?: string) => {
    const currentPath = router.currentRoute.value.path
    const currentQuery = router.currentRoute.value.query

    router.push({
      path: currentPath,
      query: { ...currentQuery, tab },
    })
  }

  const navigateToEvaluate = (_workflowId?: string) => {
    navigateToTab('evaluate')
  }

  const navigateToTrace = (_workflowId?: string) => {
    navigateToTab('agent-trace')
  }

  const navigateToCriteria = (_workflowId?: string) => {
    navigateToTab('criteria')
  }

  const navigateToResults = (_workflowId?: string) => {
    navigateToTab('results')
  }

  return {
    navigateToTab,
    navigateToEvaluate,
    navigateToTrace,
    navigateToCriteria,
    navigateToResults,
  }
}
