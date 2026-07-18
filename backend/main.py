import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from api.router import api_router
from core.config import settings
from db.session import engine

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting CropPilot backend", environment=settings.ENVIRONMENT)
    from db.session import init_db
    await init_db()
    from telemetry.otel import setup_opentelemetry
    setup_opentelemetry(app)
    from rag.ingestion import ingest_scheme_data
    try:
        count = await ingest_scheme_data()
        logger.info("Scheme data ingested", count=count)
    except Exception as e:
        logger.warning("Scheme ingestion skipped", error=str(e))
    yield
    await engine.dispose()
    logger.info("CropPilot backend stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-Cloud RAG & Telemetry Backend for CropPilot",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

from middleware.structured_logging import StructuredLoggingMiddleware
from middleware.metrics import PrometheusMiddleware

app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(PrometheusMiddleware)

app.include_router(api_router)

# Mount the prometheus_client exporter on /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
    }
