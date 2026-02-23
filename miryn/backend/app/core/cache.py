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
    Append a JSON-serializable event to the Redis list for a user and set the list's time-to-live.
    
    Parameters:
        user_id (str): Identifier used to form the Redis key "events:{user_id}".
        event (dict): Event payload to be JSON-serialized; datetime/date values are converted to ISO strings.
        ttl_seconds (int): Time-to-live for the Redis key in seconds (default 3600).
    
    Notes:
        The function returns without raising on any error (errors are suppressed).
    """
    key = f"events:{user_id}"
    try:
        redis_client.rpush(key, json.dumps(event, default=_json_default))
        redis_client.expire(key, ttl_seconds)
    except Exception:
        return


def drain_events(user_id: str, limit: int = 100) -> list:
    """
    Remove up to `limit` JSON-encoded events for `user_id` from Redis and return them as Python objects.
    
    Attempts to LPOP up to `limit` items from the Redis list at key "events:{user_id}", decodes bytes to UTF-8, parses each item with `json.loads`, and collects successfully parsed objects in a list. Stops early if the list is empty. If any unexpected exception occurs while accessing Redis, returns an empty list.
    
    Parameters:
    	user_id (str): Identifier of the user whose event list will be drained.
    	limit (int): Maximum number of events to pop and return.
    
    Returns:
    	events (list): List of parsed JSON objects popped from the user's events list; may be empty.
    """
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
