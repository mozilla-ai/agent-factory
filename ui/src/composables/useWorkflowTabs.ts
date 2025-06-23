import { computed } from 'vue'
import { useTabs } from './useTabs'
import type { EvaluationStatus } from '@/types'

// Import tab components
import AgentFileExplorer from '@/components/tabs/AgentFileExplorer.vue'
import AgentEvaluationPanel from '@/components/tabs/AgentEvaluationPanel.vue'
import AgentEvalTraceViewer from '@/components/tabs/AgentEvalTraceViewer.vue'
import EvaluationCriteriaViewer from '@/components/tabs/EvaluationCriteriaViewer.vue'
import EvaluationResultsViewer from '@/components/tabs/EvaluationResultsViewer.vue'

export function useWorkflowTabs(evaluationStatus: EvaluationStatus | undefined) {
  const { activeTab, setActiveTab } = useTabs('files')

  // Dynamic tab list based on evaluation status
  const availableTabs = computed(() => {
    const tabs = [
      { id: 'files', label: 'Files' },
      { id: 'evaluate', label: 'Run Evaluation' },
    ]

    if (evaluationStatus?.hasAgentTrace) {
      tabs.push({ id: 'agent-trace', label: 'Agent Trace' })
    }

    tabs.push({ id: 'criteria', label: 'Evaluation Criteria' })

    if (evaluationStatus?.hasEvalResults) {
      tabs.push({ id: 'results', label: 'Evaluation Results' })
    }

    return tabs
  })

  // Dynamic component loading based on active tab
  const currentTabComponent = computed(() => {
    switch (activeTab.value) {
      case 'files':
        return AgentFileExplorer
      case 'evaluate':
        return AgentEvaluationPanel
      case 'agent-trace':
        return AgentEvalTraceViewer
      case 'criteria':
        return EvaluationCriteriaViewer
      case 'results':
        return EvaluationResultsViewer
      default:
        return AgentFileExplorer
    }
  })

  return {
    activeTab,
    setActiveTab,
    availableTabs,
    currentTabComponent,
  }
}
