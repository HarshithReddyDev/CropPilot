from opentelemetry import trace, baggage
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

from core.config import settings
from db.session import engine

class BaggageSpanProcessor(SpanProcessor):
    def on_start(self, span, parent_context=None):
        b = baggage.get_all(context=parent_context)
        if b:
            for key, value in b.items():
                span.set_attribute(key, value)

    def on_end(self, span):
        pass

def setup_opentelemetry(app):
    resource = Resource.create({
        "service.name": settings.OTEL_SERVICE_NAME,
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.ENVIRONMENT,
    })

    tracer_provider = TracerProvider(
        resource=resource,
        sampler=ParentBasedTraceIdRatio(
            float(settings.OTEL_TRACES_SAMPLER_ARG)
        ),
    )
    
    tracer_provider.add_span_processor(BaggageSpanProcessor())

    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            headers=settings.OTEL_EXPORTER_OTLP_HEADERS,
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(otlp_exporter)
        )

    from opentelemetry.sdk.trace.export import ConsoleSpanExporter
    if settings.DEBUG:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

    trace.set_tracer_provider(tracer_provider)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    return tracer_provider
