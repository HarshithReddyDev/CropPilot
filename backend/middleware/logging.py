import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)

        elapsed = time.perf_counter() - start_time
        response.headers["X-Request-ID"] = request_id

        if elapsed > 1.0:
            print(
                f"SLOW_REQUEST: method={request.method} path={request.url.path} "
                f"elapsed={elapsed:.3f}s request_id={request_id}"
            )

        return response
