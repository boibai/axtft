from functools import lru_cache
import redis
from app.core.config import REDIS_URL

@lru_cache
def get_redis_client():
    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True
    )