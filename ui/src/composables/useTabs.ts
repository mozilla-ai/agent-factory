import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export function useTabs(defaultTab: string = 'files') {
  const route = useRoute()
  const router = useRouter()
  const activeTab = ref<string>((route.query.tab as string) || defaultTab)

  // Set active tab and update URL
  function setActiveTab(tab: string): void {
    activeTab.value = tab

    // Update URL to preserve tab when refreshing
    router.replace({
      path: route.path,
      query: { ...route.query, tab },
    })
  }

  // Sync with route changes
  watch(
    () => route.query.tab,
    (newTab) => {
      if (newTab && typeof newTab === 'string') {
        activeTab.value = newTab
      }
    },
  )

  return {
    activeTab,
    setActiveTab,
  }
}
