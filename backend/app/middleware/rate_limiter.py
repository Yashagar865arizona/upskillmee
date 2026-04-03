"""
Simple rate limiter middleware using Redis
"""

from fastapi import HTTPException, Request
from redis import Redis
import time
from functools import lru_cache

@lru_cache()
def get_redis():
    return Redis(host='localhost', port=6379, db=0)

class RateLimiter:
    def __init__(self, requests_per_minute: int = 10):
        self.redis = get_redis()
        self.requests_per_minute = requests_per_minute
        self.window = 60  # 1 minute window

    async def check_rate_limit(self, request: Request):
        if request.client is None:
            # If client info is not available, use a default IP
            client_ip = "0.0.0.0"
        else:
            client_ip = request.client.host

        current = int(time.time())
        window_key = f"{client_ip}:{current // self.window}"

        try:
            # Get current request count
            requests = await self.redis.incr(window_key)

            # Set expiry if this is a new key
            if requests == 1:
                await self.redis.expire(window_key, self.window)

            # Check if we've exceeded the limit
            if int(requests) > self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later."
                )

            return requests
        except Exception as e:
            # If Redis is down, log the error but allow the request
            logger.warning(f"Rate limiter error: {e}")
