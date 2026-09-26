# CropPilot system architecture

This diagram describes the current local/development architecture, not a
multi-cloud production deployment. The frontend is run separately; the
Docker Compose stack runs the API, database, workers and observability.

```mermaid
flowchart LR
  Farmer[Farmer / advisor] --> Browser[Next.js web app]
  Browser -->|typed REST / SSE / WebSocket| API[FastAPI API]

  subgraph Services[Backend service layer]
    API --> Market[Market Intelligence]
    API --> Weather[Weather service]
    API --> Map[Map / agricultural context]
    API --> Disease[Disease diagnosis]
    API --> Agent[LangGraph assistant]
    API --> Schemes[Scheme / farm services]
  end

  subgraph Data[PostgreSQL]
    PG[(PostgreSQL)]
    GIS[(PostGIS market geography)]
    Vector[(pgvector RAG / assistant memory)]
    PG --- GIS
    PG --- Vector
  end
  Market --> PG
  Map --> GIS
  Map --> PG
  Disease --> PG
  Agent --> Vector
  Agent --> PG

  subgraph Async[Async jobs]
    Beat[Celery Beat] --> Worker[Celery workers]
    Worker --> PG
  end

  Agent --> Router[Assistant provider router]
  Router --> Ollama[Local Ollama, optional]
  Router -. optional configured provider .-> Hosted[Hosted LLM provider]
  Disease --> Registry[License/evidence-gated model registry]
  Registry --> Models[Lazy bounded specialist cache]

  Market --> AG[AGMARKNET data]
  Weather --> OM[Open-Meteo]
  Map --> OSM[Nominatim / OSM]
  Map --> SG[SoilGrids WCS]
  Map -. unavailable / not integrated .-> Gov[CGWB / CWC / IMD / OGD]

  API --> OTEL[OpenTelemetry]
  Worker --> OTEL
  OTEL --> Prom[Prometheus]
  Prom --> Grafana[Grafana]
```

## Current implementation boundaries

- PostgreSQL is the operational database. PostGIS stores verified market
  coordinates and supports geographic queries; pgvector backs assistant/RAG
  retrieval.
- Market, weather, map, disease, scheme and assistant capabilities remain
  separate backend services behind typed API routes.
- Celery worker/beat handle asynchronous jobs; model artifacts are loaded
  lazily and cached, not loaded wholesale at API startup.
- Optional hosted assistant providers are operator-configured; local Ollama
  can be used. A paid hosted model is not a required product dependency.
- SoilGrids WCS is queried server-side and cached. CGWB groundwater, CWC
  reservoir storage, IMD station rainfall and OGD crop statistics are not
  integrated in the current environment; their UI sections report unavailable.
- OpenTelemetry/Prometheus/Grafana are in the local Compose stack.

## Future deployment

Containerized API/worker replicas, managed PostgreSQL/PostGIS/pgvector,
object storage, regional caches and autoscaled CPU/GPU inference are future
options. They are not represented as current deployed infrastructure.
