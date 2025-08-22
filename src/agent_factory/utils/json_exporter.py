import json
from pathlib import Path

from any_agent.tracing.agent_trace import AgentSpan
from any_agent.tracing.attributes import GenAI
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.trace import format_trace_id

KEEP_SPANS_WITH_ANY_AGENT_OPERATION_NAME = ["call_llm", "execute_tool", "invoke_agent"]


class JsonFileSpanExporter(SpanExporter):
    def __init__(self, output_dir: str | Path = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path.cwd()
        if not self.output_dir.exists():
            self.output_dir.mkdir(exist_ok=True, parents=True)

    def export(self, spans: list[ReadableSpan]) -> None:
        # File name matches how trace_id will be formatted inside the JSON
        output_file = self.output_dir / f"0x{format_trace_id(spans[0].context.trace_id)}.jsonl"

        for span in spans:
            # We don't need a2a server events in traces
            if span.attributes.get(GenAI.OPERATION_NAME) in KEEP_SPANS_WITH_ANY_AGENT_OPERATION_NAME:
                with output_file.open("a", encoding="utf-8") as f:
                    try:
                        agent_span = AgentSpan.from_otel(span)
                        f.write(agent_span.model_dump_json() + "\n")
                    except (json.JSONDecodeError, TypeError, AttributeError):
                        f.write(json.dumps({"error": "Could not serialize span", "span_str": str(span)}) + "\n")

    def shutdown(self):
        pass
