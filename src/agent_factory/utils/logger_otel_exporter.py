# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading
import typing

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


class LoggerExporter(SpanExporter):
    """Implementation of :class:`.SpanExporter` that puts spans in a logger."""

    def __init__(self, logger) -> None:
        self._logger = logger
        self._stopped = False
        self._lock = threading.Lock()

    def export(self, spans: typing.Sequence[ReadableSpan]) -> SpanExportResult:
        """Stores a list of spans in memory."""
        if self._stopped:
            return SpanExportResult.FAILURE
        with self._lock:
            for span in spans:
                self._logger.info(span.to_json(indent=None))
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        """Shut downs the exporter.

        Calls to export after the exporter has been shut down will fail.
        """
        self._stopped = True

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
