// Transform results to align with criteria
export const transformResults = (data: any) => {
  // If it's already in the old format, return it as is
  if (data?.checkpoints) {
    return data
  }

  // Transform from new format to old format
  return {
    // Add metadata from new format if available
    totalScore: data?.obtained_score || 0,
    maxPossibleScore: data?.max_score || 0,

    // Transform checkpoint results to match the expected format
    checkpoints:
      data?.checkpoint_results?.map((checkpoint: any) => ({
        result: checkpoint.passed ? 'pass' : 'fail',
        feedback: checkpoint.reason,
        criteria: checkpoint.criteria,
        points: checkpoint.points,
      })) || [],
  }
}
