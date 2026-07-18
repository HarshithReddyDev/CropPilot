import time
import uuid
import structlog

logger = structlog.get_logger()


class StructuredLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request_id = str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        start_time = time.perf_counter()

        status_code = [500]

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = time.perf_counter() - start_time
            client = scope.get("client")
            client_host = client[0] if client else None
            
            logger.info(
                "request_completed",
                method=scope.get("method"),
                path=scope.get("path"),
                status_code=status_code[0],
                elapsed_ms=round(elapsed * 1000, 2),
                request_id=request_id,
                client_host=client_host,
            )
