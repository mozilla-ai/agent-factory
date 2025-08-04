from pathlib import Path

from any_agent.callbacks import Callback
from any_agent.callbacks.context import Context


class SaveAgentTraceCallback(Callback):
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def after_agent_invocation(self, context: Context, *args, **kwargs) -> Context:
        agent_trace_save_path = self.output_dir / "factory_agent_trace.json"
        with agent_trace_save_path.open("w", encoding="utf-8") as f:
            f.write(context.trace.model_dump_json(indent=2, serialize_as_any=True))

        return context
