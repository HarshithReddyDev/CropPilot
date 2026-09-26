# Scalability and multi-cloud evolution

This document separates the current local Compose setup from a possible
future distributed deployment. Dashed connections in the diagram are
future options, not services currently deployed.

## Current implementation

```mermaid
flowchart LR
  Browser[Next.js frontend, run separately] --> API[FastAPI container]
  API --> PG[(PostgreSQL + PostGIS + pgvector)]
  API --> Worker[Celery worker / beat]
  Worker --> PG
  API --> Ollama[Optional local Ollama]
  API --> Obs[OTel collector]
  Obs --> Prom[Prometheus]
  Prom --> Grafana[Grafana]
```

Current scaling primitives include containerized API/workers, typed service
boundaries, PostgreSQL/PostGIS indexes, pgvector, bounded/lazy model loading,
provider routing, caching, background jobs and observability. No measured
multi-region throughput or autoscaling claim is made.

## Future multi-cloud option (not implemented)

```mermaid
flowchart LR
  User[Users] --> CDN[CDN / edge frontend]
  CDN -. future .-> LB[Managed load balancer]
  LB -. future .-> API1[FastAPI replicas]
  LB -. future .-> API2[FastAPI replicas]
  API1 --> Queue[Managed queue / Celery broker]
  API2 --> Queue
  Queue --> CPU[CPU worker pool]
  Queue -. optional GPU jobs .-> GPU[GPU inference workers]
  API1 --> Cache[Regional cache]
  API2 --> Cache
  API1 --> DB[(Managed PostgreSQL + PostGIS + pgvector)]
  API2 --> DB
  CPU --> DB
  GPU --> Object[Object storage for explicitly retained artifacts]
  API1 -. OTel .-> Obs[OpenTelemetry collector]
  CPU -. OTel .-> Obs
  Obs --> Metrics[Prometheus-compatible metrics / Grafana]
```

The same containerized FastAPI/Celery interfaces could be deployed on AWS,
Azure, Google Cloud or compatible infrastructure. Database, object storage,
queue, cache, CDN, container platform and observability exporters would need
provider-specific adapters/configuration. Vendor portability is a design
goal, not a claim that the current system is deployed across clouds.

## Growth path

1. **Small:** current single-host Compose; local PostgreSQL and bounded workers.
2. **Medium:** managed PostgreSQL/PostGIS, separate API replicas, external
   cache/queue and worker concurrency limits.
3. **Large:** partition high-volume observations by geography/time where
   measured query patterns justify it; regional ingestion/cache; dedicated
   CPU/GPU inference workers; CDN for frontend/static assets.
4. **Multi-region:** regional read/query services and data replication only
   after data-residency, freshness and consistency requirements are defined.

PostGIS supports geographic filters and indexes. Existing services already
bound market/map requests and cache slowly changing soil/district context;
future scaling must retain provider rate limits, provenance, model license
gates and honest unavailable states. No cloud cost, capacity or availability
SLA is asserted here.
