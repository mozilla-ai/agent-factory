// File names
export const FILE_NAMES = {
  AGENT: 'agent.py',
  EVALUATION_CASE: 'evaluation_case.yaml',
  EVALUATION_RESULTS: 'evaluation_results.json',
  AGENT_EVAL_TRACE: 'agent_eval_trace.json',
} as const

// Default values
export const DEFAULTS = {
  AGENT_PROMPT: 'Summarize text content from a given webpage URL',
} as const

// Process IDs
export const PROCESS_IDS = {
  AGENT_FACTORY: 'agent-factory',
} as const

// API Messages
export const MESSAGES = {
  SUCCESS: {
    AGENT_COMPLETED: '[agent-factory] Workflow completed successfully.',
    AGENT_RUN_COMPLETED:
      '[Agent run completed. Generated agent_eval_trace.json]',
    EVALUATION_CASES_COMPLETED:
      '[Evaluation cases generation completed. Saved to evaluation_case.yaml]',
    EVALUATION_COMPLETED:
      '[Agent evaluation completed. Results saved to evaluation_results.json]',
  },
  ERROR: {
    AGENT_TRACE_NOT_FOUND:
      'Agent trace file not found. Make sure to run the agent first.',
    EVALUATION_CASES_NOT_FOUND:
      'Evaluation cases not found. Make sure to generate evaluation cases first.',
  },
} as const
