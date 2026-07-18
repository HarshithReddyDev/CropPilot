import time
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    "croppilot_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "croppilot_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"]
)

# Example gauges (can be updated elsewhere in the app or via a background task)
DB_CONNECTIONS = Gauge(
    "croppilot_db_connections_active",
    "Active Database Connections"
)

CELERY_QUEUE = Gauge(
    "croppilot_celery_queue_size",
    "Celery Queue Size",
    ["queue"]
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        method = request.method
        # We simplify path to avoid high cardinality (e.g. replacing IDs)
        # But for the simulation, exact path is fine.
        path = request.url.path
        
        # Don't track metrics for /metrics itself
        if path == "/metrics":
            return await call_next(request)

        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception as e:
            status_code = "500"
            raise e
        finally:
            process_time = time.time() - start_time
            REQUEST_COUNT.labels(method=method, path=path, status_code=status_code).inc()
            REQUEST_LATENCY.labels(method=method, path=path).observe(process_time)
            
            # Dummy update for DB connections (just for simulation sake)
            # In a real app, this would be updated from the connection pool stats
            DB_CONNECTIONS.set(5)
            CELERY_QUEUE.labels(queue="default").set(12)

        return response
