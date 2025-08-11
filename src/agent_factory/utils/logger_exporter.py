from opentelemetry.sdk.trace.export import SpanExporter


class LoggerSpanExporter(SpanExporter):
    def __init__(self, logger) -> None:
        self.logger = logger

    def export(self, spans):
        for span in spans:
            self.logger.info(span.to_json())

    def shutdown(self):
        pass
