import json
from datetime import date, datetime
from typing import Any

import redis
from redis import Redis

from app.config import settings


redis_client: Redis = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


def get_cache() -> Redis:
    return redis_client


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def publish_event(user_id: str, event: dict, ttl_seconds: int = 3600) -> None:
    key = f"events:{user_id}"
    try:
        redis_client.rpush(key, json.dumps(event, default=_json_default))
        redis_client.expire(key, ttl_seconds)
    except Exception:
        return


def drain_events(user_id: str, limit: int = 100) -> list:
    key = f"events:{user_id}"
    events = []
    try:
        for _ in range(limit):
            item = redis_client.lpop(key)
            if not item:
                break
            if isinstance(item, bytes):
                item = item.decode("utf-8")
            try:
                events.append(json.loads(item))
            except Exception:
                continue
    except Exception:
        return []
    return events


def enqueue_job(queue: str, payload: dict, ttl_seconds: int = 3600) -> None:
    key = f"jobs:{queue}"
    try:
        redis_client.rpush(key, json.dumps(payload, default=_json_default))
        redis_client.expire(key, ttl_seconds)
    except Exception:
        return
