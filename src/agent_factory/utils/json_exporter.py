import json
from pathlib import Path

from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.trace import format_trace_id


class JsonFileSpanExporter(SpanExporter):
    def __init__(self, output_dir):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path.cwd()
        if not self.output_dir.exists():
            self.output_dir.mkdir(exist_ok=True, parents=True)

    def export(self, spans) -> None:
        # File name matches how trace_id will be formatted inside the JSON
        output_file = self.output_dir / f"0x{format_trace_id(spans[0].context.trace_id)}.json"
        try:
            all_spans = json.loads(output_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            all_spans = []

        for span in spans:
            # We don't need a2a server events in traces
            if not span.name.startswith("a2a.server"):
                try:
                    span_data = json.loads(span.to_json())
                except (json.JSONDecodeError, TypeError, AttributeError):
                    span_data = {"error": "Could not serialize span", "span_str": str(span)}

                all_spans.append(span_data)

        output_file.write_text(json.dumps(all_spans, indent=2))

    def shutdown(self):
        pass
