"""Shared utilities for OpenTelemetry tracing setup."""

from pathlib import Path

from opentelemetry import trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from agent_factory.utils.json_exporter import JsonFileSpanExporter


def setup_tracing(traces_dir: Path, service_name: str, instrument_httpx: bool = True) -> trace.Tracer:
    """Set up OpenTelemetry tracing with JSON file export.
    
    Args:
        traces_dir: Directory to save trace files
        service_name: Name of the service for the tracer
        instrument_httpx: Whether to instrument HTTPX client
        
    Returns:
        Configured tracer instance
    """
    # Ensure traces directory exists
    traces_dir.mkdir(exist_ok=True, parents=True)
    
    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider())
    
    # Add JSON file exporter
    span_processor = SimpleSpanProcessor(JsonFileSpanExporter(traces_dir))
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrument HTTPX if requested
    if instrument_httpx:
        HTTPXClientInstrumentor().instrument()
    
    return trace.get_tracer(service_name)