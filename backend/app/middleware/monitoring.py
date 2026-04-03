from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ..monitoring.metrics import embedding_metrics
import time

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        
        if request.url.path.startswith("/api/v1/embeddings"):
            duration = time.time() - start_time
            embedding_metrics.record_api_latency(duration)
        
        return response 