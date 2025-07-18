from pathlib import Path

from any_agent.tracing.agent_trace import AgentTrace
from pydantic import BaseModel


class ExecutionCosts(BaseModel):
    input_cost: float
    output_cost: float
    total_cost: float


class AgentTraceWithExecutionCosts(AgentTrace):
    execution_costs: ExecutionCosts


def load_agent_trace(agent_trace_json_file: str | Path) -> AgentTraceWithExecutionCosts:
    """Loads and validates an AgentTrace from the specified JSON file.

    Args:
        agent_trace_json_file: The path to the agent trace JSON file.

    Returns:
        A validated AgentTrace object.
    """
    file_path = Path(agent_trace_json_file)
    with file_path.open(encoding="utf-8") as f:
        agent_trace_data = f.read()
        agent_trace = AgentTraceWithExecutionCosts.model_validate_json(agent_trace_data)
    return agent_trace
