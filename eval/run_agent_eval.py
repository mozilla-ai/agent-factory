from any_agent.evaluation.evaluate import evaluate
from any_agent.evaluation.evaluation_case import EvaluationCase
from any_agent.tracing.agent_trace import AgentTrace

evaluation_case = EvaluationCase.from_yaml("generated_workflows/evaluation_case.yaml")

# Load agent trace from output.json
with open("generated_workflows/agent_trace.json", encoding="utf-8") as f:
    agent_trace = AgentTrace.model_validate_json(f.read())

eval_result = evaluate(
    evaluation_case=evaluation_case,
    trace=agent_trace,
)

print(f"Final score: {eval_result.score}")
print(f"Checkpoint results: {eval_result.checkpoint_results}")
