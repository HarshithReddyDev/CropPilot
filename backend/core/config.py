from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "CropPilot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # PostgreSQL
    POSTGRES_USER: str = "croppilot"
    POSTGRES_PASSWORD: str = "croppilot"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "croppilot"
    DATABASE_URL: str | None = None
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_PRE_PING: bool = True

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def db_url_sync(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # OpenTelemetry
    OTEL_SERVICE_NAME: str = "croppilot-backend"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_EXPORTER_OTLP_HEADERS: str = ""
    OTEL_TRACES_SAMPLER: str = "parentbased_traceidratio"
    OTEL_TRACES_SAMPLER_ARG: str = "1.0"
    OTEL_METRICS_EXPORTER: str = "prometheus"
    OTEL_LOGS_EXPORTER: str = "otlp"

    # Langfuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # Celery
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 100

    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.db_url_sync

    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.db_url_sync

    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    AWS_S3_BUCKET: str = "croppilot-media"
    AWS_ECS_CLUSTER: str = "croppilot-cluster"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # H3
    H3_RESOLUTION: int = 8

    # Disease Detection
    YOLO_MODEL_PATH: str = "/models/best.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    MAX_DETECTIONS: int = 100

    # Weather Cache
    WEATHER_CACHE_TTL: int = 1800
    FORECAST_CACHE_TTL: int = 3600

    # Market Price Cache
    MARKET_PRICE_CACHE_TTL: int = 3600

    SCHEMES_VECTOR_COLLECTION: ClassVar[str] = "government_schemes"

    # Logging
    LOG_LEVEL: str = "INFO"
    STRUCTURED_LOGGING: bool = True


settings = Settings()
