import json

import redis
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import Span


class RedisSpanExporter(SpanExporter):
    """A SpanExporter that writes spans to a Redis list."""

    def __init__(self, redis_host="redis", redis_port=6379, redis_list="otel-spans"):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        self.redis_list = redis_list

    def export(self, spans: tuple[Span, ...]) -> SpanExportResult:
        """Exports a batch of spans to Redis."""
        try:
            for span in spans:
                span_json = json.dumps(self._span_to_dict(span))
                self.redis_client.rpush(self.redis_list, span_json)
            return SpanExportResult.SUCCESS
        except Exception as e:
            print(f"Error exporting spans to Redis: {e}")
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        """Shuts down the exporter."""
        self.redis_client.close()

    def _span_to_dict(self, span: Span) -> dict:
        """Converts a Span object to a dictionary."""
        return {
            "name": span.name,
            "context": {
                "trace_id": span.context.trace_id,
                "span_id": span.context.span_id,
                "is_remote": span.context.is_remote,
            },
            "parent_id": span.parent.span_id if span.parent else None,
            "start_time": span.start_time,
            "end_time": span.end_time,
            "attributes": dict(span.attributes),
            "events": [
                {
                    "name": event.name,
                    "attributes": dict(event.attributes),
                    "timestamp": event.timestamp,
                }
                for event in span.events
            ],
            "status": {
                "status_code": span.status.status_code.name,
                "description": span.status.description,
            },
            "kind": span.kind.name,
        }
