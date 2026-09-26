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
    # How long Ollama keeps a loaded model resident (e.g. "30m", "0" to
    # unload immediately). Previously only read from a .env key nothing
    # consumed; now an explicit setting sent with every Ollama request.
    OLLAMA_KEEP_ALIVE: str = "10m"

    # Assistant (single bounded LangGraph agent; local-first, no key required)
    ASSISTANT_ENABLED: bool = True
    ASSISTANT_LLM_MODE: str = "hybrid"
    ASSISTANT_PROVIDER_ORDER: str = "gemini,openrouter,groq,ollama"
    ASSISTANT_LOCAL_MODEL: str = "qwen3:8b"
    ASSISTANT_LOCAL_FALLBACK_MODEL: str = "qwen3:4b"
    ASSISTANT_MAX_TOOL_STEPS: int = 5
    ASSISTANT_REQUEST_TIMEOUT: int = 60
    ASSISTANT_PROVIDER_COOLDOWN_SECONDS: int = 300
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = ""
    OPENROUTER_FREE_ROUTER: bool = False
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    # OpenRouter free-model tiering: deterministic ordered fallback across
    # operator-configured FREE models, then Ollama. Budgets are LOCAL
    # application caps (not provider quotas); provider 429/402 moves tiers
    # regardless. Empty TIER_N_MODEL disables that tier. A tier model must
    # end in ":free" or it is rejected at load (never silently route paid).
    ASSISTANT_OPENROUTER_TIERING_ENABLED: bool = False
    ASSISTANT_OPENROUTER_TIER_1_MODEL: str = ""
    ASSISTANT_OPENROUTER_TIER_1_MAX_REQUESTS: int = 20
    ASSISTANT_OPENROUTER_TIER_1_MAX_TOKENS: int = 100000
    ASSISTANT_OPENROUTER_TIER_1_TOOL_CALLING: bool = True
    ASSISTANT_OPENROUTER_TIER_1_MAX_CONTEXT: int = 0
    ASSISTANT_OPENROUTER_TIER_2_MODEL: str = ""
    ASSISTANT_OPENROUTER_TIER_2_MAX_REQUESTS: int = 20
    ASSISTANT_OPENROUTER_TIER_2_MAX_TOKENS: int = 100000
    ASSISTANT_OPENROUTER_TIER_2_TOOL_CALLING: bool = True
    ASSISTANT_OPENROUTER_TIER_2_MAX_CONTEXT: int = 0
    ASSISTANT_OPENROUTER_TIER_3_MODEL: str = ""
    ASSISTANT_OPENROUTER_TIER_3_MAX_REQUESTS: int = 20
    ASSISTANT_OPENROUTER_TIER_3_MAX_TOKENS: int = 100000
    ASSISTANT_OPENROUTER_TIER_3_TOOL_CALLING: bool = True
    ASSISTANT_OPENROUTER_TIER_3_MAX_CONTEXT: int = 0
    # Conservative completion-token reservation held per in-flight request
    # and reconciled against actual provider usage afterwards.
    ASSISTANT_OPENROUTER_TOKEN_RESERVE: int = 2000
    # Daily budget bucket timezone. UTC aligns with OpenRouter's own
    # free-quota reset (UTC midnight).
    ASSISTANT_USAGE_TIMEZONE: str = "UTC"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    ASSISTANT_ENABLE_VOICE: bool = True
    ASSISTANT_ASR_ENGINE: str = "faster-whisper"
    ASSISTANT_ASR_FALLBACK: str = ""
    ASSISTANT_ASR_MODEL: str = "base"
    ASSISTANT_ASR_DEVICE: str = "auto"
    ASSISTANT_TTS_ENGINE: str = "auto"
    ASSISTANT_TTS_MODEL: str = "ai4bharat/indic-parler-tts"
    ASSISTANT_TTS_DEVICE: str = "auto"
    ASSISTANT_TTS_TIMEOUT_S: int = 30
    ASSISTANT_TTS_MAX_CHARS: int = 2000
    ASSISTANT_VOICE_ENABLED: bool = True
    ASSISTANT_TTS_FALLBACK: str = ""
    ASSISTANT_DEFAULT_LANGUAGE: str = "en"
    ASSISTANT_AUTO_LANGUAGE_DETECTION: bool = True
    ASSISTANT_AUTO_SPEAK: bool = False
    ASSISTANT_MT_DEVICE: str = "auto"
    ASSISTANT_MT_CONCURRENCY: int = 1
    ASSISTANT_MT_TIMEOUT_S: int = 60
    ASSISTANT_MT_MODEL: str = ""
    ASSISTANT_RAG_ENABLED: bool = True
    ASSISTANT_RAG_TOP_K: int = 12
    ASSISTANT_RAG_RERANK_K: int = 5
    ASSISTANT_EMBEDDING_MODEL: str = "bge-m3"
    ASSISTANT_PERSIST_AUDIO: bool = False

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

    # Disease diagnosis platform (evidence-aware, CPU-first)
    DISEASE_ENABLED: bool = True
    DISEASE_MODEL_CACHE_DIR: str = "/models/disease"
    DISEASE_MAX_LOADED_MODELS: int = 3
    DISEASE_MAX_PARALLEL_SPECIALISTS: int = 3
    DISEASE_MODEL_LOAD_TIMEOUT: int = 120
    DISEASE_INFERENCE_TIMEOUT_SECONDS: float = 20.0
    DISEASE_MAX_IMAGE_MB: float = 10
    DISEASE_MAX_PIXELS: int = 25000000
    DISEASE_ENABLE_RESEARCH_MODELS: bool = False
    DISEASE_ENABLE_VLM_FALLBACK: bool = True
    DISEASE_ROUTER_MODE: str = "auto"
    DISEASE_ROUTER_HEAD_PATH: str = ""
    DISEASE_PROTOTYPE_INDEX_PATH: str = ""
    DISEASE_VLM_PROVIDER: str = ""
    DISEASE_VLM_MODEL: str = ""

    # Weather Cache
    WEATHER_CACHE_TTL: int = 1800
    FORECAST_CACHE_TTL: int = 3600

    # Market Price Cache
    MARKET_PRICE_CACHE_TTL: int = 3600

    # Market Intelligence. Active provider: AGMARKNET Direct (public web
    # backend, no API key). The OGD client remains dormant for future use;
    # a missing DATA_GOV_API_KEY must never break Market Intelligence.
    # OGD API key lives on the backend only. Never expose it to the frontend.
    DATA_GOV_API_KEY: str = ""
    DATA_GOV_RESOURCE_ID: str = "9ef84268-d588-465a-a308-a864a43d0070"
    DATA_GOV_BASE_URL: str = "https://api.data.gov.in/resource"
    # Active provider base URL (configurable). Public endpoints, no key.
    AGMARKNET_BASE_URL: str = "https://api.agmarknet.gov.in/v1/"
    AGMARKNET_TIMEOUT: int = 30
    # Optional deployment preference only; the product never depends on it.
    MARKET_DEFAULT_STATE: str = ""
    DATA_GOV_TIMEOUT: int = 30
    DATA_GOV_PAGE_SIZE: int = 100
    # Upper bound on records stored per ingestion run. National runs page
    # through the source and stop at this bound; increase deliberately.
    MARKET_INGEST_MAX_RECORDS: int = 20000
    # Concurrent upstream fetches per ingestion run. Storing stays
    # sequential (one DB session); keep this small to respect the source.
    MARKET_INGEST_CONCURRENCY: int = 4
    MARKET_INGEST_CRON_HOUR: int = 6
    MARKET_INGEST_CRON_MINUTE: int = 30

    # Local development convenience only. When explicitly enabled AND the
    # environment is not production, API authentication accepts requests
    # without credentials as a deterministic development identity.
    # Production always requires real JWT validation (fail closed), even if
    # this flag is set. Never enable outside local development.
    DEV_AUTH_BYPASS: bool = False

    @property
    def dev_auth_bypass_active(self) -> bool:
        return bool(self.DEV_AUTH_BYPASS) and self.ENVIRONMENT.strip().lower() != "production"

    SCHEMES_VECTOR_COLLECTION: ClassVar[str] = "government_schemes"

    # Logging
    LOG_LEVEL: str = "INFO"
    STRUCTURED_LOGGING: bool = True


settings = Settings()
