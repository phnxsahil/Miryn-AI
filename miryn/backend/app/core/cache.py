import json
from datetime import date, datetime
from typing import Any
from uuid import uuid4

import redis
from redis import Redis

from app.config import settings


redis_client: Redis = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    # Redis is optional here, so an absent server must fail in well under a
    # second. Without these, every cache read spent seconds retrying a refused
    # connection before the caller gave up.
    socket_connect_timeout=0.5,
    socket_timeout=0.5,
    retry_on_timeout=False,
)


def get_cache() -> Redis:
    """
    Retrieve the module's shared Redis client.
    
    Returns:
        Redis: The global Redis client instance used for cache and queue operations.
    """
    return redis_client


def _json_default(value: Any) -> str:
    """
    Return an ISO 8601 string for date/datetime values, otherwise the value's string representation.
    
    Converts datetime and date objects to their ISO 8601 representation via isoformat(). For all other inputs, returns the result of str(value).
    
    Parameters:
        value: The value to convert to a string.
    
    Returns:
        A string: ISO 8601 for date/datetime inputs, or `str(value)` for other types.
    """
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def publish_event(user_id: str, event: dict, ttl_seconds: int = 3600) -> None:
    """
    Publish an event to connected tabs and retain a short reconnect backlog.
    
    Parameters:
        user_id (str): Identifier used to form the Redis key "events:{user_id}".
        event (dict): Event payload to be JSON-serialized; datetime/date values are converted to ISO strings.
        ttl_seconds (int): Retained for caller compatibility; the reconnect backlog lives for 300 seconds.
    
    Notes:
        The function returns without raising on any error (errors are suppressed).
    """
    try:
        encoded = json.dumps({**event, "id": event.get("id") or str(uuid4())}, default=_json_default)
        key = f"events_backlog:{user_id}"
        redis_client.rpush(key, encoded)
        redis_client.ltrim(key, -50, -1)
        redis_client.expire(key, 300)
        redis_client.publish(f"events:{user_id}", encoded)
    except Exception:
        return


def enqueue_job(queue: str, payload: dict, ttl_seconds: int = 3600) -> None:
    """
    Enqueue a job payload into a Redis list named "jobs:{queue}" and set an expiration on that list.
    
    Parameters:
    	queue (str): Queue identifier used to form the Redis key "jobs:{queue}".
    	payload (dict): JSON-serializable job payload; datetime and date objects are converted to ISO strings.
    	ttl_seconds (int): Time-to-live for the Redis list in seconds; the key will expire after this many seconds.
    
    Notes:
    	If an error occurs while interacting with Redis, the function returns silently without raising.
    """
    key = f"jobs:{queue}"
    try:
        redis_client.rpush(key, json.dumps(payload, default=_json_default))
        redis_client.expire(key, ttl_seconds)
    except Exception:
        return
