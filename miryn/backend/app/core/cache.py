import redis
from redis import Redis
from app.config import settings


redis_client: Redis = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)


def get_cache() -> Redis:
    return redis_client
