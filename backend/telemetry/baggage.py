from opentelemetry import baggage
from opentelemetry.context import Context
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace import ReadableSpan


class BaggageSpanProcessor(SpanProcessor):
    def on_start(self, span: ReadableSpan, parent_context: Context | None = None):
        if parent_context:
            farmer_id = baggage.get_baggage("farmer_id", context=parent_context)
            h3_index = baggage.get_baggage("h3_index", context=parent_context)
            if farmer_id:
                span.set_attribute("farmer.id", farmer_id)
            if h3_index:
                span.set_attribute("h3.spatial_index", h3_index)

    def on_end(self, span: ReadableSpan):
        pass
